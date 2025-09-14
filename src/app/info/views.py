import asyncio
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils import imdb
from .schemas.media import MediaRead
from .services import MediaService


async def imdb_info(media_data: MediaRead, db: AsyncSession):
    media_service = MediaService(db)
    media = await media_service.read_or_create(media_data)

    return JSONResponse(media.model_dump(mode="json"))


async def related_media(id: str, lang: str):
    media = await imdb.get_media(id, lang)
    related = await media.get_related_media()
    related = [item.to_json() for item in related]

    return JSONResponse(related)


async def search(term: str, lang: str, db: AsyncSession):
    media_service = MediaService(db)
    results = await imdb.search(term, lang, ids_only=True)
    objects = []
    for id in results:
        media_data = MediaRead(imdb_code=id, lang=lang)
        media = await media_service.read_or_create(media_data)
        objects.append(media)

    results = [result.model_dump(mode="json") for result in objects]
    return JSONResponse(results)
