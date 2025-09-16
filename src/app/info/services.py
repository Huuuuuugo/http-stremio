import asyncio

import aiohttp
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.utils import imdb
from .models import Movie, Series, Episode
from .schemas.movie import MovieCreate
from .schemas.series import SeriesCreate
from .schemas.episode import EpisodeCreate
from .schemas.media import MediaRead


class MovieService:
    class Exceptions:
        class MovieAlreadyExists(Exception):
            """A record with the specified imdb code and language already existes"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def create(self, movie_data: MovieCreate) -> Movie:
        try:
            movie = Movie(**movie_data.model_dump())
            self.db.add(movie)

            async with self.db_lock:
                await self.db.flush()

            return movie

        except IntegrityError as e:
            if "UNIQUE" in e.args[0]:
                await self.db.rollback()
                msg = "A record with the specified imdb code and language already existes"
                raise self.Exceptions.MovieAlreadyExists(msg)
            raise e

    async def read(self, movie_data: MediaRead) -> Movie | None:
        stmt = select(Movie).where(
            and_(
                Movie.imdb_code == movie_data.imdb_code,
                Movie.lang == movie_data.lang,
            )
        )
        results = await self.db.execute(stmt)
        movie = results.scalar()

        return movie


class SeriesService:
    class Exceptions:
        class SeriesAlreadyExists(Exception):
            """A record with the specified imdb code and language already existes"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def create(self, series_data: SeriesCreate) -> Series:
        try:
            series = Series(**series_data.model_dump())
            self.db.add(series)

            async with self.db_lock:
                await self.db.flush()

            return series

        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE" in e.args[0]:
                msg = "A record with the specified imdb code and language already existes"
                raise self.Exceptions.SeriesAlreadyExists(msg)
            raise e

    async def read(self, series_data: MediaRead) -> Series | None:
        stmt = select(Series).where(
            and_(
                Series.imdb_code == series_data.imdb_code,
                Series.lang == series_data.lang,
            )
        )
        results = await self.db.execute(stmt)
        series = results.scalar()

        return series


class EpisodeService:
    class Exceptions:
        class SeriesNotFound:
            """No record found for a series with specified params"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, series_data: MediaRead, episode_data: EpisodeCreate) -> Episode:
        stmt = select(Series).where(
            and_(
                Series.imdb_code == series_data.imdb_code,
                Series.lang == series_data.lang,
            )
        )
        results = await self.db.execute(stmt)
        series = results.scalar()

        if series is None:
            msg = "No record found for a series with specified params"
            raise self.Exceptions.SeriesNotFound(msg)

        return await self.create_with_series(series, episode_data)

    async def create_with_series(self, series: Series, episode_data: EpisodeCreate) -> Episode:
        episode = Episode(**episode_data.model_dump())
        episode.series = series
        self.db.add(episode)

        return episode


class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def read_or_create(self, media_data: MediaRead) -> Movie | Series:
        try:
            movie_service = MovieService(self.db)
            series_service = SeriesService(self.db)
            movie = await movie_service.read(media_data)
            series = await series_service.read(media_data)

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
                        async with self.db_lock:
                            movie = await movie_service.create(movie_data)

                        return movie

                    case "series":
                        series_data = SeriesCreate(
                            imdb_code=media_data.imdb_code,
                            lang=media_data.lang,
                            name=media.title,
                            year=media.year,
                            end_year=media.end_year,
                            media_type=media.type,
                            synopsis=media.synopsis,
                            rating=media.rating,
                            poster=media.poster,
                            logo=f"https://live.metahub.space/logo/medium/{media_data.imdb_code}/img",
                            background=f"https://live.metahub.space/background/medium/{media_data.imdb_code}/img",
                        )
                        async with self.db_lock:
                            series = await series_service.create(series_data)

                        # TODO: update this to scrape data from imdb
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"https://cinemeta-live.strem.io/meta/series/{media_data.imdb_code}.json") as response:
                                stremio_info = await response.json()

                        try:
                            episode_service = EpisodeService(self.db)
                            tasks = []
                            for episode in stremio_info["meta"]["videos"]:
                                episode_data = EpisodeCreate(
                                    season=episode["season"],
                                    episode=episode["episode"],
                                    name=episode["title"],
                                    synopsis=episode["overview"],
                                    image=episode["thumbnail"],
                                )
                                tasks.append(episode_service.create_with_series(series, episode_data))

                            await asyncio.gather(*tasks)

                        except KeyError:
                            pass

                        return series

        except movie_service.Exceptions.MovieAlreadyExists:
            movie = await movie_service.read(media_data)
            return movie

        except series_service.Exceptions.SeriesAlreadyExists:
            series = await series_service.read(media_data)
            return series
