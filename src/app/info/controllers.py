from fastapi import APIRouter, Request

from .views import imdb_info, related_media, search

router = APIRouter(prefix="/info", tags=["info"])


@router.get("/{lang}/imdb/")
async def imdb_info_route(id: str, lang: str):
    return await imdb_info(id, lang)


@router.get("/{lang}/imdb/related-media/")
async def imdb_related_media_route(lang: str, id: str):
    return await related_media(id, lang)


@router.get("/{lang}/search/")
async def serach_route(term: str, lang: str):
    return await search(term, lang)
