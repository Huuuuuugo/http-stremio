from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db
from .types import LangChoices
from .views import imdb_info, related_media, search
from .schemas.media import MediaRead


router = APIRouter(prefix="/info", tags=["info"])


@router.get("/{lang}/imdb/{imdb_code}/")
async def imdb_info_route(media_data: MediaRead = Depends(), db: AsyncSession = Depends(get_db)):
    return await imdb_info(media_data, db)


@router.get("/{lang}/imdb/related-media/")
async def imdb_related_media_route(lang: LangChoices, id: str):
    return await related_media(id, lang)


@router.get("/{lang}/search/")
async def serach_route(term: str, lang: LangChoices, db: AsyncSession = Depends(get_db)):
    return await search(term, lang, db)
