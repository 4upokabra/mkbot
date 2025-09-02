from typing import List, Dict, Any, Optional
from ..db import get_conn


def _map_row(row) -> Dict[str, Any]:
	return {
		"id": row[0],
		"subject_id": row[1],
		"title": row[2],
		"description": row[3] or "",
		"due_date": row[4],
		"created_by": row[5],
		"created_at": row[6],
	}


async def add_homework(subject_id: str, title: str, description: str, due_date_iso: str, created_by: Optional[int]) -> None:
	conn = get_conn()
	await conn.execute(
		"INSERT INTO homeworks (subject_id, title, description, due_date, created_by) VALUES (?, ?, ?, ?, ?)",
		(subject_id, title, description, due_date_iso, created_by),
	)
	await conn.commit()


async def list_all(limit: int = 50) -> List[Dict[str, Any]]:
	cur = await get_conn().execute(
		"SELECT id, subject_id, title, description, due_date, created_by, created_at FROM homeworks ORDER BY due_date ASC, id DESC LIMIT ?",
		(limit,),
	)
	rows = await cur.fetchall()
	return [_map_row(r) for r in rows]


async def list_by_date(due_date_iso: str) -> List[Dict[str, Any]]:
	cur = await get_conn().execute(
		"SELECT id, subject_id, title, description, due_date, created_by, created_at FROM homeworks WHERE due_date=? ORDER BY id DESC",
		(due_date_iso,),
	)
	rows = await cur.fetchall()
	return [_map_row(r) for r in rows]


async def list_by_subject(subject_id: str, limit: int = 50) -> List[Dict[str, Any]]:
	cur = await get_conn().execute(
		"SELECT id, subject_id, title, description, due_date, created_by, created_at FROM homeworks WHERE subject_id=? ORDER BY due_date ASC, id DESC LIMIT ?",
		(subject_id, limit),
	)
	rows = await cur.fetchall()
	return [_map_row(r) for r in rows]


async def delete_due_before(threshold_iso_date: str) -> int:
	conn = get_conn()
	cur = await conn.execute("DELETE FROM homeworks WHERE due_date < ?", (threshold_iso_date,))
	await conn.commit()
	return cur.rowcount if cur.rowcount != -1 else 0
