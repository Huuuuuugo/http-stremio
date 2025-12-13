import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import MovieSource, SeriesSource
from .schemas import (
    MovieSourceCreate,
    SeriesSourceCreate,
    MovieSourceRead,
    SeriesSourceRead,
    MovieSourceBase,
    SeriesSourceBase,
)
from .db import init_db

asyncio.run(init_db())


class StaticSourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def add(self, data: MovieSourceCreate | SeriesSourceCreate):
        if isinstance(data, MovieSourceCreate):
            source = MovieSource(**data.model_dump())
            self.db.add(source)
            await self.db.commit()
        else:
            source = SeriesSource(**data.model_dump())
            self.db.add(source)
            await self.db.commit()

    async def read(self, data: MovieSourceRead | SeriesSourceRead) -> list[MovieSourceBase] | list[SeriesSourceBase]:
        if isinstance(data, MovieSourceRead):
            stmt = select(MovieSource).where(MovieSource.code == data.code)
            results = await self.db.execute(stmt)
            results = [MovieSourceBase.model_validate(result) for result in results.scalars().all()]

        else:
            stmt = select(SeriesSource).where(
                SeriesSource.code == data.code,
                SeriesSource.season == data.season,
                SeriesSource.episode == data.episode,
            )
            results = await self.db.execute(stmt)
            results = [SeriesSourceBase.model_validate(result) for result in results.scalars().all()]

        return results
