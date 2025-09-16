import asyncio
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils import imdb
from .models import Movie
from .schemas.media import MediaRead
from .schemas.movie import MovieBase
from .schemas.series import SeriesBase
from .services import MediaService


async def imdb_info(media_data: MediaRead, db: AsyncSession):
    media_service = MediaService(db)
    media = await media_service.read_or_create(media_data)

    await db.commit()

    await db.refresh(media)
    if isinstance(media, Movie):
        result = MovieBase.model_validate(media).model_dump(mode="json")
    else:
        result = SeriesBase.model_validate(media).model_dump(mode="json")

    return JSONResponse(result)


async def related_media(id: str, lang: str):
    media = await imdb.get_media(id, lang)
    related = await media.get_related_media()
    related = [item.to_json() for item in related]

    return JSONResponse(related)


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
            results.append(MovieBase.model_validate(model).model_dump(mode="json"))
        else:
            results.append(SeriesBase.model_validate(model).model_dump(mode="json"))

    return JSONResponse(results)
