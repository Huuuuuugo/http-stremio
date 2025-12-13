import asyncio
from typing import Literal

from . import scraper as imdb
from .db import SessionLocal, init_db
from .models import Movie
from .schemas.media import MediaRead
from .schemas.movie import MovieBaseTranslated
from .schemas.series import SeriesBaseTranslated
from .services import MediaService
from .types import LangChoices

asyncio.run(init_db())


async def get_media(
    imdb_code: str,
    lang: Literal["en", "fr", "de", "es", "pt", "ja", "zh"] = "en",
) -> MovieBaseTranslated | SeriesBaseTranslated:
    media_data = MediaRead(imdb_code=imdb_code, lang=lang)  # type: ignore
    async with SessionLocal() as db:
        media_service = MediaService(db)
        media = await media_service.read_or_create(media_data)

        await db.commit()

        await db.refresh(media)
        if isinstance(media, Movie):
            result = MovieBaseTranslated.from_movie_model(media, media_data.lang)
        else:
            result = SeriesBaseTranslated.from_series_model(media, media_data.lang)

    return result


async def get_related_media(
    imdb_code: str,
    lang: Literal["en", "fr", "de", "es", "pt", "ja", "zh"] = "en",
) -> list[MovieBaseTranslated | SeriesBaseTranslated]:
    media_data = MediaRead(imdb_code=imdb_code, lang=lang)  # type: ignore
    async with SessionLocal() as db:
        media_service = MediaService(db)
        related_media = await media_service.get_related(media_data)

        await db.commit()

        results = []
        for media in related_media:
            await db.refresh(media)
            if isinstance(media, Movie):
                results.append(MovieBaseTranslated.from_movie_model(media, media_data.lang))
            else:
                results.append(SeriesBaseTranslated.from_series_model(media, media_data.lang))

    return results


async def search(
    term: str,
    lang: Literal["en", "fr", "de", "es", "pt", "ja", "zh"] = "en",
) -> list[MovieBaseTranslated | SeriesBaseTranslated]:
    async with SessionLocal() as db:
        media_service = MediaService(db)
        results = await imdb.search(term, lang, ids_only=True)
        tasks = []
        for id in results:
            media_data = MediaRead(imdb_code=id, lang=lang)  # type: ignore
            tasks.append(media_service.read_or_create(media_data))

        models = await asyncio.gather(*tasks)

        await db.commit()

        results = []
        for model in models:
            await db.refresh(model)
            if isinstance(model, Movie):
                results.append(MovieBaseTranslated.from_movie_model(model, LangChoices(lang)))
            else:
                results.append(SeriesBaseTranslated.from_series_model(model, LangChoices(lang)))

    return results
