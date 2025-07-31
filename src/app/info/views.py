import aiohttp
from fastapi.responses import JSONResponse

from src.utils import imdb
from src.app import config


async def imdb_info(id: str, lang: str):
    media = await imdb.get_media(id, lang)
    info_dict = {
        "id": media.id,
        "title": media.title,
        "year": media.year,
        "type": media.type,
        "synopsis": media.synopsis,
        "rating": media.rating,
        "poster": media.poster,
        "logo": f"https://live.metahub.space/logo/medium/{id}/img",
        "background": f"https://live.metahub.space/background/medium/{id}/img",
    }

    # TODO: update this to use imdb data instead of stremio's
    if info_dict["type"] == "series":
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://cinemeta-live.strem.io/meta/series/{id}.json") as response:
                stremio_info = await response.json()

        info_dict.update({"episodes": stremio_info["meta"]["videos"]})

    return JSONResponse(info_dict)


async def related_media(id: str, lang: str):
    media = await imdb.get_media(id, lang)
    related = await media.get_related_media()
    related = [item.to_json() for item in related]

    return JSONResponse(related)


async def search(term: str, lang: str):
    results = await imdb.search(term, lang)
    results = [result.to_json() for result in results]

    return JSONResponse(results)
