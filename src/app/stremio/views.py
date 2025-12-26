import asyncio

from fastapi.responses import JSONResponse

from ... import static_sources
from src.scrapers import pobreflix
from . import constants
from .services import stream_cache
from src.utils.stremio import StremioStreamManager


async def addon_manifest():
    return JSONResponse(constants.MANIFEST)


async def movie_stream(id: str, proxy_url: None | str = None):
    cached_streams, invalid_sources = await stream_cache.get(id)

    if cached_streams:
        stream_manager = StremioStreamManager()
        for stream in cached_streams:
            stream_manager.append(stream)
        return JSONResponse(stream_manager.to_dict())

    tasks = [
        pobreflix.movie_streams(id, proxy_url=proxy_url),
        static_sources.movie_streams(id, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)

    stream_manager = StremioStreamManager()
    for result in results:
        stream_manager.extend(result)

    stream_cache.set(id, stream_manager.streams)
    return JSONResponse(stream_manager.to_dict())


async def series_stream(
    id: str, season: int, episode: int, proxy_url: None | str = None
):
    episode_id = f"{id}:{season}:{episode}"

    cached_streams, invalid_sources = await stream_cache.get(episode_id)

    if cached_streams:
        stream_manager = StremioStreamManager()
        for stream in cached_streams:
            stream_manager.append(stream)
        return JSONResponse(stream_manager.to_dict())

    # if not in cache run the scrapers
    tasks = [
        pobreflix.series_stream(id, season, episode, proxy_url=proxy_url),
        static_sources.series_stream(id, season, episode, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)

    stream_manager = StremioStreamManager()
    for result in results:
        stream_manager.extend(result)

    # cache the result
    stream_cache.set(episode_id, stream_manager.streams)

    return JSONResponse(stream_manager.to_dict())
