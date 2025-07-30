from fastapi import APIRouter, Request
from .views import addon_manifest, movie_stream, series_stream

router = APIRouter(prefix="")


@router.get("/manifest.json")
async def manifest_route(request: Request):
    return await addon_manifest()


@router.get("/stream/movie/{id}.json")
async def movie_stream_route(request: Request, id: str):
    # mount proxy and cache url with the same url used to acces the server
    scheme = request.url.scheme
    hostname = request.url.hostname
    port = request.url.port
    proxy_url = f"{scheme}://{hostname}{f":{port}" if port else ""}/proxy/stream/"

    return await movie_stream(id, proxy_url)


@router.get("/stream/series/{id}:{season}:{episode}.json")
async def series_stream_route(request: Request, id: str, season: int, episode: int):
    # mount proxy and cache url with the same url used to acces the server
    scheme = request.url.scheme
    hostname = request.url.hostname
    port = request.url.port
    proxy_url = f"{scheme}://{hostname}{f":{port}" if port else ""}/proxy/stream/"

    return await series_stream(id, season, episode, proxy_url)
