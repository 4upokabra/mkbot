import asyncio
import logging
from typing import Dict, Any

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

from .config import API_ID, API_HASH, BOT_TOKEN, load_subjects, get_tz, HW_RETENTION_DAYS
from .db import init_db
from .repositories import users as users_repo
from .repositories import homeworks as hw_repo
from .utils import dates as date_utils
from .keyboards import main_menu, admin_menu, subjects_menu, cancel_menu
from datetime import timedelta


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SUBJECTS, SUBJECT_ID_TO_NAME = load_subjects()
TZINFO = get_tz()

# Простая in-memory FSM
user_states: Dict[int, Dict[str, Any]] = {}


def is_admin(user_id: int) -> bool:
	return users_repo.is_admin(user_id)


def format_homework_item(item: Dict[str, Any]) -> str:
	subject_name = SUBJECT_ID_TO_NAME.get(item["subject_id"], item["subject_id"]) \
		if item.get("subject_id") else ""
	due = date_utils.from_iso(item["due_date"]).strftime("%d.%m.%Y")
	parts = [
		f"📌 {subject_name}: {item['title']}",
		f"🗓 На дату: {due}",
	]
	if item.get("description"):
		parts.append(f"📝 {item['description']}")
	return "\n".join(parts)


def format_homeworks_list(items: list[Dict[str, Any]]) -> str:
	if not items:
		return "Ничего не найдено."
	return "\n\n".join(format_homework_item(i) for i in items)


async def run_periodic_cleanup() -> None:
	while True:
		try:
			# Удаляем все ДЗ, дата которых строго меньше порога
			today = date_utils.today_in_tz(TZINFO)
			threshold = today if HW_RETENTION_DAYS <= 0 else (today - timedelta(days=HW_RETENTION_DAYS))
			deleted = await hw_repo.delete_due_before(date_utils.to_iso(threshold))
			if deleted:
				logger.info("Auto-cleanup removed %s old homeworks", deleted)
		except Exception as e:
			logger.exception("Cleanup error: %s", e)
		await asyncio.sleep(60 * 60)


async def main() -> None:
	client = TelegramClient("bot", API_ID, API_HASH)
	await init_db()
	await client.start(bot_token=BOT_TOKEN)
	logger.info("Bot started")

	# запустить авто-очистку в фоне
	asyncio.create_task(run_periodic_cleanup())

	@client.on(events.NewMessage(pattern="/start"))
	async def handler_start(event: events.NewMessage.Event):
		user = await event.get_sender()
		await users_repo.upsert_and_subscribe(user.id, user.first_name or "", user.username)
		text = (
			"Привет! Ты подписан на уведомления.\n"
			"Выбери действие в меню ниже:"
		)
		await event.respond(text, buttons=main_menu())

	@client.on(events.NewMessage(pattern="/admin_menu"))
	async def handler_admin_menu(event: events.NewMessage.Event):
		user = await event.get_sender()
		if not is_admin(user.id):
			await event.respond("У вас нет доступа к админ-меню.")
			return
		await event.respond("Админ-меню:", buttons=admin_menu())

	@client.on(events.CallbackQuery)
	async def handler_callbacks(event: events.CallbackQuery.Event):
		data = event.data.decode("utf-8", errors="ignore")
		user = await event.get_sender()
		user_id = user.id
		state = user_states.get(user_id)

		try:
			if data == "MENU:ALL":
				items = await hw_repo.list_all()
				await event.answer()
				await event.respond("Все ДЗ:\n\n" + format_homeworks_list(items))
			elif data == "MENU:TOMORROW":
				tomorrow = date_utils.tomorrow_in_tz(TZINFO)
				items = await hw_repo.list_by_date(date_utils.to_iso(tomorrow))
				await event.answer()
				await event.respond("ДЗ на завтра:\n\n" + format_homeworks_list(items))
			elif data == "MENU:BY_DATE":
				user_states[user_id] = {"flow": "USER_BY_DATE"}
				await event.answer()
				await event.respond("Введите дату в формате дд.мм.гггг", buttons=cancel_menu())
			elif data == "MENU:BY_SUBJECT":
				await event.answer()
				await event.respond("Выберите предмет:", buttons=subjects_menu(SUBJECTS))
			elif data.startswith("SUBJECT:"):
				subject_id = data.split(":", 1)[1]
				if state and state.get("flow") == "ADMIN_ADD" and state.get("step") == "SUBJECT":
					# продвигаем шаг админ-добавления
					state["data"] = {"subject_id": subject_id}
					state["step"] = "TITLE"
					await event.answer()
					await event.respond("Введите название задания (например: ДЗ, Типовой и т.д.)", buttons=cancel_menu())
				else:
					items = await hw_repo.list_by_subject(subject_id)
					await event.answer()
					await event.respond(
						f"ДЗ по предмету {SUBJECT_ID_TO_NAME.get(subject_id, subject_id)}:\n\n" + format_homeworks_list(items)
					)
			elif data == "BACK:MAIN":
				await event.answer()
				await event.respond("Главное меню:", buttons=main_menu())
			elif data == "ADMIN:ADD_HW":
				if not is_admin(user_id):
					await event.answer("Нет доступа", alert=True)
					return
				user_states[user_id] = {"flow": "ADMIN_ADD", "step": "SUBJECT", "data": {}}
				await event.answer()
				await event.respond("Выберите предмет для ДЗ:", buttons=subjects_menu(SUBJECTS))
			elif data == "ADMIN:BROADCAST":
				if not is_admin(user_id):
					await event.answer("Нет доступа", alert=True)
					return
				user_states[user_id] = {"flow": "ADMIN_BROADCAST", "step": "TEXT"}
				await event.answer()
				await event.respond("Введите текст рассылки", buttons=cancel_menu())
			elif data == "ACTION:CANCEL":
				user_states.pop(user_id, None)
				await event.answer("Отменено")
				await event.respond("Действие отменено.", buttons=main_menu())
			else:
				await event.answer()
		except Exception as e:
			logger.exception("Error in callback handler: %s", e)
			await event.answer("Произошла ошибка", alert=True)

	@client.on(events.NewMessage)
	async def handler_messages(event: events.NewMessage.Event):
		user = await event.get_sender()
		user_id = user.id
		text = (event.raw_text or "").strip()
		state = user_states.get(user_id)
		if not state:
			return

		flow = state.get("flow")
		try:
			if flow == "USER_BY_DATE":
				maybe = date_utils.parse_user_date(text)
				if not maybe:
					await event.respond("Неверный формат. Введите дату как дд.мм.гггг", buttons=cancel_menu())
					return
				items = await hw_repo.list_by_date(date_utils.to_iso(maybe))
				user_states.pop(user_id, None)
				await event.respond("Результаты:\n\n" + format_homeworks_list(items), buttons=main_menu())

			elif flow == "ADMIN_ADD":
				step = state.get("step")
				if step == "TITLE":
					state["data"]["title"] = text
					state["step"] = "DESC"
					await event.respond("Введите описание задания", buttons=cancel_menu())
				elif step == "DESC":
					state["data"]["description"] = text
					state["step"] = "DUE"
					await event.respond("Введите дату на которую это задание (дд.мм.гггг)", buttons=cancel_menu())
				elif step == "DUE":
					maybe = date_utils.parse_user_date(text)
					if not maybe:
						await event.respond("Неверный формат даты. Введите дд.мм.гггг", buttons=cancel_menu())
						return
					payload = state["data"]
					await hw_repo.add_homework(
						payload["subject_id"],
						payload.get("title", "Задание"),
						payload.get("description", ""),
						date_utils.to_iso(maybe),
						user_id,
					)
					user_states.pop(user_id, None)
					await event.respond("ДЗ добавлено ✅", buttons=admin_menu() if is_admin(user_id) else main_menu())

			elif flow == "ADMIN_BROADCAST":
				# ожидаем текст и рассылаем
				user_states.pop(user_id, None)
				await event.respond("Начинаю рассылку…")
				user_ids = await users_repo.get_all_subscribed_user_ids()
				sent = 0
				errors = 0
				for uid in user_ids:
					try:
						await event.client.send_message(uid, text)
						sent += 1
					except FloodWaitError as fw:
						await asyncio.sleep(int(fw.seconds) + 1)
						try:
							await event.client.send_message(uid, text)
							sent += 1
						except Exception:
							errors += 1
					except Exception:
						errors += 1
				await event.respond(f"Рассылка завершена. Успехов: {sent}, ошибок: {errors}")
		except Exception as e:
			logger.exception("Error in message handler: %s", e)
			await event.respond("Произошла ошибка при обработке сообщения")

	await client.run_until_disconnected()


if __name__ == "__main__":
	asyncio.run(main())
