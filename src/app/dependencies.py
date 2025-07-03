from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
