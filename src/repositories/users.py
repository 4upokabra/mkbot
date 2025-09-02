from typing import List
from ..db import get_conn
from ..config import ADMIN_WHITELIST


async def upsert_and_subscribe(user_id: int, first_name: str, username: str | None) -> None:
	conn = get_conn()
	await conn.execute(
		"""
		INSERT INTO users (user_id, first_name, username, is_subscribed)
		VALUES (?, ?, ?, 1)
		ON CONFLICT(user_id) DO UPDATE SET
			first_name=excluded.first_name,
			username=excluded.username,
			is_subscribed=1
		""",
		(user_id, first_name, username),
	)
	await conn.commit()


async def get_all_subscribed_user_ids() -> List[int]:
	cur = await get_conn().execute("SELECT user_id FROM users WHERE is_subscribed=1")
	rows = await cur.fetchall()
	return [int(r[0]) for r in rows]


async def unsubscribe(user_id: int) -> None:
	conn = get_conn()
	await conn.execute("UPDATE users SET is_subscribed=0 WHERE user_id=?", (user_id,))
	await conn.commit()


def is_admin(user_id: int) -> bool:
	return user_id in ADMIN_WHITELIST
