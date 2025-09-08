from typing import List
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from ..db import get_session, User
from ..config import ADMIN_WHITELIST


async def upsert_and_subscribe(user_id: int, first_name: str, username: str | None) -> None:
	async with get_session() as session:
		stmt = pg_insert(User).values(
			user_id=user_id,
			first_name=first_name,
			username=username,
			is_subscribed=True,
		)
		stmt = stmt.on_conflict_do_update(
			index_elements=[User.user_id],
			set_={
				"first_name": stmt.excluded.first_name,
				"username": stmt.excluded.username,
				"is_subscribed": True,
			},
		)
		await session.execute(stmt)
		await session.commit()


async def get_all_subscribed_user_ids() -> List[int]:
	async with get_session() as session:
		result = await session.execute(select(User.user_id).where(User.is_subscribed.is_(True)))
		return [int(row[0]) for row in result.all()]


async def unsubscribe(user_id: int) -> None:
	async with get_session() as session:
		user = await session.get(User, user_id)
		if user:
			user.is_subscribed = False
			await session.commit()


def is_admin(user_id: int) -> bool:
	return user_id in ADMIN_WHITELIST
