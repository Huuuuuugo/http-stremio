from fastapi import APIRouter, Depends

from .views import imdb_info, related_media, search
from src.scrapers.imdb.schemas.media import MediaRead
from src.scrapers.imdb.types import LangChoices


router = APIRouter(prefix="/info", tags=["info"])


@router.get("/{lang}/imdb/{imdb_code}/")
async def imdb_info_route(media_data: MediaRead = Depends()):
    return await imdb_info(media_data)


@router.get("/{lang}/imdb/{imdb_code}/related-media/")
async def imdb_related_media_route(media_data: MediaRead = Depends()):
    return await related_media(media_data)


@router.get("/{lang}/search/")
async def serach_route(term: str, lang: LangChoices):
    return await search(term, lang.value)
