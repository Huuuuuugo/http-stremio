from typing import Literal
from fastapi.responses import JSONResponse

from src.scrapers import imdb
from src.scrapers.imdb.schemas.media import MediaRead


async def imdb_info(media_data: MediaRead):
    media = await imdb.get_media(media_data.imdb_code, media_data.lang.value)

    return JSONResponse(media.model_dump(mode="json"))


async def related_media(media_data: MediaRead):
    related_media = await imdb.get_related_media(media_data.imdb_code, media_data.lang.value)

    return JSONResponse([media.model_dump(mode="json") for media in related_media])


async def search(term: str, lang: Literal["en", "fr", "de", "es", "pt", "ja", "zh"]):
    results = await imdb.search(term, lang)

    return JSONResponse([result.model_dump(mode="json") for result in results])
