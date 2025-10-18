import asyncio
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils import imdb
from .models import Movie
from .schemas.media import MediaRead
from .schemas.movie import MovieBaseTranslated
from .schemas.series import SeriesBaseTranslated
from .services import MediaService


async def imdb_info(media_data: MediaRead, db: AsyncSession):
    media_service = MediaService(db)
    media = await media_service.read_or_create(media_data)

    await db.commit()

    await db.refresh(media)
    if isinstance(media, Movie):
        result = MovieBaseTranslated.from_movie_model(media, media_data.lang).model_dump(mode="json")
    else:
        result = SeriesBaseTranslated.from_series_model(media, media_data.lang).model_dump(mode="json")

    return JSONResponse(result)


async def related_media(media_data: MediaRead, db: AsyncSession):
    media_service = MediaService(db)
    related_media = await media_service.get_related(media_data)

    await db.commit()

    results = []
    for media in related_media:
        await db.refresh(media)
        if isinstance(media, Movie):
            results.append(MovieBaseTranslated.from_movie_model(media, media_data.lang).model_dump(mode="json"))
        else:
            results.append(SeriesBaseTranslated.from_series_model(media, media_data.lang).model_dump(mode="json"))

    return JSONResponse(results)


async def search(term: str, lang: str, db: AsyncSession):
    media_service = MediaService(db)
    results = await imdb.search(term, lang, ids_only=True)
    tasks = []
    for id in results:
        media_data = MediaRead(imdb_code=id, lang=lang)
        tasks.append(media_service.read_or_create(media_data))

    models = await asyncio.gather(*tasks)

    await db.commit()

    results = []
    for model in models:
        await db.refresh(model)
        if isinstance(model, Movie):
            results.append(MovieBaseTranslated.from_movie_model(model, lang).model_dump(mode="json"))
        else:
            results.append(SeriesBaseTranslated.from_series_model(model, lang).model_dump(mode="json"))

    return JSONResponse(results)
