from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env", override=True)


def _async_url_to_sync(async_url: str) -> str:
    if async_url.startswith("postgresql+asyncpg://"):
        rest = async_url.removeprefix("postgresql+asyncpg://")
        return f"postgresql+psycopg2://{rest}"
    if async_url.startswith("postgresql://"):
        rest = async_url.removeprefix("postgresql://")
        return f"postgresql+psycopg2://{rest}"
    raise ValueError(
        "DATABASE_URL must start with postgresql+asyncpg:// or postgresql:// when SYNC_DATABASE_URL is omitted."
    )


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f'{name} is not set. Copy .env.example to .env next to docker-compose.yml '
            "and set POSTGRES_USER and POSTGRES_PASSWORD (or set DATABASE_URL)."
        )
    return value


def _resolve_database_urls() -> tuple[str, str]:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        sync_url = os.getenv("SYNC_DATABASE_URL") or _async_url_to_sync(database_url)
        return database_url, sync_url

    user = _require("POSTGRES_USER")
    password = _require("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DB", "AI-accounting")

    async_u = URL.create(
        drivername="postgresql+asyncpg",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    sync_u = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return async_u.render_as_string(hide_password=False), sync_u.render_as_string(hide_password=False)


DATABASE_URL, SYNC_DATABASE_URL = _resolve_database_urls()

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = None


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
