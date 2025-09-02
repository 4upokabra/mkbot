from telethon import Button
from typing import List, Dict


def main_menu():
	return [
		[Button.inline("📚 Все ДЗ", b"MENU:ALL"), Button.inline("📅 На завтра", b"MENU:TOMORROW")],
		[Button.inline("🔎 По дате", b"MENU:BY_DATE"), Button.inline("📖 По предмету", b"MENU:BY_SUBJECT")],
	]


def admin_menu():
	return [
		[Button.inline("➕ Добавить ДЗ", b"ADMIN:ADD_HW")],
		[Button.inline("📣 Рассылка", b"ADMIN:BROADCAST")],
	]


def subjects_menu(subjects: List[Dict[str, str]]):
	rows = []
	row = []
	for item in subjects:
		row.append(Button.inline(item["name"], f"SUBJECT:{item['id']}".encode()))
		if len(row) == 2:
			rows.append(row)
			row = []
	if row:
		rows.append(row)
	rows.append([Button.inline("⬅️ Назад", b"BACK:MAIN")])
	return rows


def cancel_menu():
	return [[Button.inline("❌ Отмена", b"ACTION:CANCEL")]]
