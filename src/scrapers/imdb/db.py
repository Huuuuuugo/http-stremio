from pathlib import Path
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

IMDB_CACHE_DB_PATH = Path(__file__).parent / "sqlite.imdb.db"
DATABASE_URL = f"sqlite+aiosqlite:///{str(IMDB_CACHE_DB_PATH)}?timeout=30"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
