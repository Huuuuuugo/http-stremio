import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.utils import imdb
from .models import Movie, Series, Episode
from .schemas.movie import MovieBase, MovieCreate
from .schemas.series import SeriesBase, SeriesCreate
from .schemas.media import MediaRead


class MovieService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, movie_data: MovieCreate) -> MovieBase:
        movie = Movie(**movie_data.model_dump())
        self.db.add(movie)
        await self.db.commit()

        await self.db.refresh(movie)
        return MovieBase.model_validate(movie)

    async def read(self, movie_data: MediaRead) -> MovieBase:
        stmt = select(Movie).where(
            and_(
                Movie.imdb_code == movie_data.imdb_code,
                Movie.lang == movie_data.lang,
            )
        )
        results = await self.db.execute(stmt)
        movie = results.scalar()

        if movie is None:
            return None

        await self.db.refresh(movie)
        return MovieBase.model_validate(movie)


class SeriesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, series_data: SeriesCreate):
        series = Series(**series_data.model_dump())
        self.db.add(series)
        await self.db.commit()

        await self.db.refresh(series)
        return SeriesBase.model_validate(series)

    async def read(self, movie_data: MediaRead) -> SeriesBase:
        stmt = select(Series).where(
            and_(
                Series.imdb_code == movie_data.imdb_code,
                Series.lang == movie_data.lang,
            )
        )
        results = await self.db.execute(stmt)
        series = results.scalar()

        if series is None:
            return None

        await self.db.refresh(series)
        return SeriesBase.model_validate(series)


class EpisodeService:
    def __init__(self, db: AsyncSession):
        self.db = db


class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def read_or_create(self, media_data: MediaRead) -> MovieBase | SeriesBase:
        movie_service = MovieService(self.db)
        series_service = SeriesService(self.db)
        movie, series = await asyncio.gather(
            movie_service.read(media_data),
            series_service.read(media_data),
        )

        if movie is not None:
            return movie
        elif series is not None:
            return series
        else:
            media = await imdb.get_media(media_data.imdb_code, media_data.lang.value)

            match media.type:
                case "movie":
                    movie_data = MovieCreate(
                        imdb_code=media_data.imdb_code,
                        lang=media_data.lang,
                        name=media.title,
                        year=media.year,
                        media_type=media.type,
                        synopsis=media.synopsis,
                        rating=media.rating,
                        poster=media.poster,
                        logo=f"https://live.metahub.space/logo/medium/{media_data.imdb_code}/img",
                        background=f"https://live.metahub.space/background/medium/{media_data.imdb_code}/img",
                    )
                    movie = await movie_service.create(movie_data)

                    return movie

                case "series":
                    series_data = SeriesCreate(
                        imdb_code=media_data.imdb_code,
                        lang=media_data.lang,
                        name=media.title,
                        start_year=media.year,
                        end_year=media.end_year,
                        media_type=media.type,
                        synopsis=media.synopsis,
                        rating=media.rating,
                        poster=media.poster,
                        logo=f"https://live.metahub.space/logo/medium/{media_data.imdb_code}/img",
                        background=f"https://live.metahub.space/background/medium/{media_data.imdb_code}/img",
                    )
                    series = await series_service.create(series_data)

                    return series
