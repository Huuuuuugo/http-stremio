import asyncio

import aiohttp
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.utils import imdb
from .models import TranslatableMovieInfo, Movie, TranslatableSeriesInfo, Series, Episode
from .schemas.movie import MovieCreate, TranslatableMovieInfoCreate
from .schemas.series import SeriesCreate, TranslatableSeriesInfoCreate
from .schemas.episode import EpisodeCreate
from .schemas.media import MediaRead


class MovieService:
    class Exceptions:
        class MovieAlreadyExists(Exception):
            """A record with the specified imdb code already exists"""

        class MovieTranslationAlreadyExists(Exception):
            """A record with the specified translation language already exists for this media"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def create(self, movie_data: MovieCreate) -> Movie:
        try:
            movie = Movie(**movie_data.model_dump())
            self.db.add(movie)

            async with self.db_lock:
                await self.db.flush([movie])

            return movie

        except IntegrityError as e:
            if "UNIQUE" in e.args[0]:
                await self.db.rollback()
                msg = "A record with the specified imdb code already exists"
                raise self.Exceptions.MovieAlreadyExists(msg)
            raise e

    async def add_translation(self, movie: Movie, translation_data: TranslatableMovieInfoCreate) -> Movie:
        try:
            translation = TranslatableMovieInfo(**translation_data.model_dump())
            translation.movie = movie

            self.db.add(translation)

            async with self.db_lock:
                await self.db.flush([translation])

            return movie

        except IntegrityError as e:
            if "UNIQUE" in e.args[0]:
                await self.db.rollback()
                msg = "A record with the specified translation language already exists for this media"
                raise self.Exceptions.MovieTranslationAlreadyExists(msg)
            raise e

    async def read(self, imdb_code: str) -> Movie | None:
        stmt = select(Movie).where(
            and_(
                Movie.imdb_code == imdb_code,
            )
        )
        results = await self.db.execute(stmt)
        movie = results.scalar()

        return movie


class SeriesService:
    class Exceptions:
        class SeriesAlreadyExists(Exception):
            """A record with the specified imdb code already exists"""

        class SeriesTranslationAlreadyExists(Exception):
            """A record with the specified translation language already exists for this media"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.db_lock = asyncio.Lock()

    async def create(self, series_data: SeriesCreate) -> Series:
        try:
            series = Series(**series_data.model_dump())
            self.db.add(series)

            async with self.db_lock:
                await self.db.flush([series])

            return series

        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE" in e.args[0]:
                msg = "A record with the specified imdb code already exists"
                raise self.Exceptions.SeriesAlreadyExists(msg)
            raise e

    async def add_translation(self, series: Series, translation_data: TranslatableSeriesInfoCreate) -> Series:
        try:
            translation = TranslatableSeriesInfo(**translation_data.model_dump())
            translation.series = series

            self.db.add(translation)

            async with self.db_lock:
                await self.db.flush([translation])

            return series

        except IntegrityError as e:
            if "UNIQUE" in e.args[0]:
                await self.db.rollback()
                msg = "A record with the specified translation language already exists for this media"
                raise self.Exceptions.SeriesTranslationAlreadyExists(msg)
            raise e

    async def read(self, imdb_code: str) -> Series | None:
        stmt = select(Series).where(
            and_(
                Series.imdb_code == imdb_code,
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
            movie = await movie_service.read(media_data.imdb_code)
            series = await series_service.read(media_data.imdb_code)

            # if the media is a movie already on the database
            if movie is not None:
                # return the movie model if the specified translation alredy exists
                for translation in movie.translations:
                    if translation.lang.value == media_data.lang.value:
                        return movie

                # save the new specified translation to the movie model before returning the movie model
                media = await imdb.get_media(media_data.imdb_code, media_data.lang.value)
                translation_data = TranslatableMovieInfoCreate(
                    lang=media_data.lang,
                    name=media.title,
                    synopsis=media.synopsis,
                    poster=media.poster,
                )
                async with self.db_lock:
                    await movie_service.add_translation(movie, translation_data)

                return movie

            # if the media is a series already on the database
            elif series is not None:
                # return the series model if the specified translation alredy exists
                for translation in series.translations:
                    if translation.lang.value == media_data.lang.value:
                        return series

                # save the new specified translation to the series model before returning the movie model
                media = await imdb.get_media(media_data.imdb_code, media_data.lang.value)
                translation_data = TranslatableSeriesInfoCreate(
                    lang=media_data.lang,
                    name=media.title,
                    synopsis=media.synopsis,
                    poster=media.poster,
                )
                async with self.db_lock:
                    await series_service.add_translation(series, translation_data)

                return series

            # if there's no media with the specified paramaters on the database
            else:
                # get movie data from imdb
                media = await imdb.get_media(media_data.imdb_code, media_data.lang.value)

                match media.type:
                    case "movie":
                        # basic movie data
                        movie_data = MovieCreate(
                            imdb_code=media_data.imdb_code,
                            year=media.year,
                            media_type=media.type,
                            rating=media.rating,
                            logo=f"https://live.metahub.space/logo/medium/{media_data.imdb_code}/img",
                            background=f"https://live.metahub.space/background/medium/{media_data.imdb_code}/img",
                        )

                        # translatable movie data
                        translation_data = TranslatableMovieInfoCreate(
                            lang=media_data.lang,
                            name=media.title,
                            synopsis=media.synopsis,
                            poster=media.poster,
                        )

                        # create movie and translation records on the database
                        async with self.db_lock:
                            movie = await movie_service.create(movie_data)
                            await movie_service.add_translation(movie, translation_data)

                        return movie

                    case "series":
                        # basic series data
                        series_data = SeriesCreate(
                            imdb_code=media_data.imdb_code,
                            year=media.year,
                            end_year=media.end_year,
                            media_type=media.type,
                            rating=media.rating,
                            logo=f"https://live.metahub.space/logo/medium/{media_data.imdb_code}/img",
                            background=f"https://live.metahub.space/background/medium/{media_data.imdb_code}/img",
                        )

                        # translatable series data
                        translation_data = TranslatableSeriesInfoCreate(
                            lang=media_data.lang,
                            name=media.title,
                            synopsis=media.synopsis,
                            poster=media.poster,
                        )

                        # create series and translation records on the database
                        async with self.db_lock:
                            series = await series_service.create(series_data)
                            await series_service.add_translation(series, translation_data)

                        # get episode data from stremio's api
                        # TODO: update this to scrape data from imdb
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"https://cinemeta-live.strem.io/meta/series/{media_data.imdb_code}.json") as response:
                                stremio_info = await response.json()

                        # create a record on the database for each episode
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

                        # skip if no episode data is found for this series
                        except KeyError:
                            pass

                        return series

        except (
            movie_service.Exceptions.MovieAlreadyExists,
            movie_service.Exceptions.MovieTranslationAlreadyExists,
        ):
            movie = await movie_service.read(media_data.imdb_code)
            return movie

        except (
            series_service.Exceptions.SeriesAlreadyExists,
            series_service.Exceptions.SeriesTranslationAlreadyExists,
        ):
            series = await series_service.read(media_data.imdb_code)
            return series
