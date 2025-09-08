from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy import select, delete
from sqlalchemy.orm import load_only
from ..db import get_session, Homework


def _map_model(hw: Homework) -> Dict[str, Any]:
	return {
		"id": hw.id,
		"subject_id": hw.subject_id,
		"title": hw.title,
		"description": hw.description or "",
		"due_date": hw.due_date.strftime("%Y-%m-%d"),
		"created_by": hw.created_by,
		"created_at": hw.created_at,
	}


async def add_homework(subject_id: str, title: str, description: str, due_date_iso: str, created_by: Optional[int]) -> None:
	async with get_session() as session:
		hw = Homework(
			subject_id=subject_id,
			title=title,
			description=description,
			due_date=date.fromisoformat(due_date_iso),
			created_by=created_by,
		)
		session.add(hw)
		await session.commit()


async def list_all(limit: int = 50) -> List[Dict[str, Any]]:
	async with get_session() as session:
		result = await session.execute(
			select(Homework).order_by(Homework.due_date.asc(), Homework.id.desc()).limit(limit)
		)
		items = result.scalars().all()
		return [_map_model(i) for i in items]


async def list_by_date(due_date_iso: str) -> List[Dict[str, Any]]:
	async with get_session() as session:
		d = date.fromisoformat(due_date_iso)
		result = await session.execute(
			select(Homework).where(Homework.due_date == d).order_by(Homework.id.desc())
		)
		items = result.scalars().all()
		return [_map_model(i) for i in items]


async def list_by_subject(subject_id: str, limit: int = 50) -> List[Dict[str, Any]]:
	async with get_session() as session:
		result = await session.execute(
			select(Homework).where(Homework.subject_id == subject_id).order_by(Homework.due_date.asc(), Homework.id.desc()).limit(limit)
		)
		items = result.scalars().all()
		return [_map_model(i) for i in items]


async def delete_due_before(threshold_iso_date: str) -> int:
	async with get_session() as session:
		threshold = date.fromisoformat(threshold_iso_date)
		result = await session.execute(delete(Homework).where(Homework.due_date < threshold).returning(Homework.id))
		deleted_rows = result.fetchall()
		await session.commit()
		return len(deleted_rows)
