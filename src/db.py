from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import BigInteger, Integer, String, Boolean, Text, Date, DateTime, func
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import DATABASE_URL


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
	first_name: Mapped[str | None] = mapped_column(String, nullable=True)
	username: Mapped[str | None] = mapped_column(String, nullable=True)
	is_subscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=func.true())
	created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Homework(Base):
	__tablename__ = "homeworks"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	subject_id: Mapped[str] = mapped_column(String, nullable=False)
	title: Mapped[str] = mapped_column(String, nullable=False)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	due_date: Mapped[Date] = mapped_column(Date, nullable=False)
	created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
	created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
	global _engine, _session_factory
	if _engine is None:
		_engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
		_session_factory = async_sessionmaker(_engine, expire_on_commit=False)
		async with _engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
	if _session_factory is None:
		raise RuntimeError("DB is not initialized. Call init_db() first.")
	async with _session_factory() as session:
		yield session
