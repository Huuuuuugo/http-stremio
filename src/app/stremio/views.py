import asyncio

from fastapi.responses import JSONResponse

from src.scrapers import pobreflix, redecanais, warezcdn
from . import constants


async def addon_manifest():
    return JSONResponse(constants.MANIFEST)


async def movie_stream(id: str, proxy_url: None | str = None, cache_url: None | str = None):
    # run scrapers
    tasks = [
        pobreflix.movie_streams(id, proxy_url=proxy_url, cache_url=cache_url),
        redecanais.movie_streams(id, proxy_url=proxy_url, cache_url=cache_url),
        warezcdn.movie_streams(id, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    return JSONResponse({"streams": streams})


async def series_stream(id: str, season: int, episode: int, proxy_url: None | str = None, cache_url: None | str = None):
    # run scrapers
    tasks = [
        pobreflix.series_stream(id, season, episode, proxy_url=proxy_url, cache_url=cache_url),
        redecanais.series_stream(id, season, episode, proxy_url=proxy_url, cache_url=cache_url),
        warezcdn.series_stream(id, season, episode, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    return JSONResponse({"streams": streams})
