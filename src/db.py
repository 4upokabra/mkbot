import os
import aiosqlite
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "bot.db")
_db_conn: Optional[aiosqlite.Connection] = None


async def init_db() -> None:
	global _db_conn
	_db_conn = await aiosqlite.connect(DB_PATH)
	await _db_conn.execute("PRAGMA journal_mode=WAL;")
	await _db_conn.execute(
		"""
		CREATE TABLE IF NOT EXISTS users (
			user_id INTEGER PRIMARY KEY,
			first_name TEXT,
			username TEXT,
			is_subscribed INTEGER NOT NULL DEFAULT 1,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
		"""
	)
	await _db_conn.execute(
		"""
		CREATE TABLE IF NOT EXISTS homeworks (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			subject_id TEXT NOT NULL,
			title TEXT NOT NULL,
			description TEXT,
			due_date TEXT NOT NULL,
			created_by INTEGER,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
		"""
	)
	await _db_conn.commit()


def get_conn() -> aiosqlite.Connection:
	if _db_conn is None:
		raise RuntimeError("DB is not initialized. Call init_db() first.")
	return _db_conn
