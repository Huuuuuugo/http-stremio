from fastapi import APIRouter, Request

from .views import static, index, redirect, movie_info, watch_movie, series_info, watch_series, search

router = APIRouter(prefix="")


@router.get("/static/{subfolder}/{file}")
async def static_route(request: Request, subfolder: str, file: str):
    headers = {key.lower(): request.headers.get(key) for key in request.headers.keys()}
    user_agent = headers.get("user-agent")
    if not user_agent:
        user_agent = ""

    return await static(subfolder, file, user_agent)


@router.get("/")
async def index_route(request: Request):
    return await index()


@router.get("/redirect")
async def redirect_route(url: str):
    return await redirect(url)


@router.get("/movie/{id}")
async def movie_info_route(request: Request, id: str):
    return await movie_info(id)


@router.get("/series/{id}")
async def series_info_redirect(request: Request, id: str):
    return await series_info(id, 1)


@router.get("/series/{id}/{season}")
async def series_info_route(request: Request, id: str, season: int):
    return await series_info(id, season)


@router.get("/watch/movie/{id}")
async def watch_movie_route(request: Request, id: str):
    # mount proxy and cache url with the same url used to acces the server
    scheme = request.url.scheme
    hostname = request.url.hostname
    port = request.url.port
    proxy_url = f"{scheme}://{hostname}{f":{port}" if port else ""}/proxy/stream/"

    return await watch_movie(id, proxy_url)


@router.get("/watch/series/{id}/{season}/{episode}")
async def watch_series_route(request: Request, id: str, season: int, episode: int):
    # mount proxy and cache url with the same url used to acces the server
    scheme = request.url.scheme
    hostname = request.url.hostname
    port = request.url.port
    proxy_url = f"{scheme}://{hostname}{f":{port}" if port else ""}/proxy/stream/"

    return await watch_series(id, season, episode, proxy_url)


@router.get("/search/")
async def search_route(term: str):
    return await search(term)
