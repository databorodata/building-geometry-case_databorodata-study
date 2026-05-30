"""Async SQLAlchemy plumbing.

This wires up an async engine + session factory and a FastAPI dependency that
yields a session. It deliberately ships with **no ORM models** — designing the
schema for saved massing options and the decision tree is part of the case study.

Add your models (e.g. a declarative `Base` and tables), create them on startup or
via migrations, and use `get_session` in your routes.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import Config


def create_engine(config: Config) -> AsyncEngine:
    return create_async_engine(config.database_url, echo=config.debug, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
