import asyncio
import json
import os
import re

import aiofiles
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from ...scrapers import pobreflix, imdb
from ... import static_sources
from .constants import TEMPLATES_DIR, STATIC_DIR
import logging

templates = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

logger = logging.getLogger(__name__)


async def static(subfolder: str, file: str, user_agent: str = ""):
    # if the tailwind css output is requested, check the browser version
    # if the browser is too old, redirect to a compatible version of the css file
    if subfolder == "css" and file == "output.css":
        matches = re.findall(r"((?:Chrome)|(?:Firefox))/(\d+)\.", user_agent)
        if matches:
            browser, version = matches[0]
            match browser:
                case "Chrome":
                    if int(version) < 57:
                        return RedirectResponse("/static/css/output.old.css")
                case "Firefox":
                    if int(version) < 52:
                        return RedirectResponse("/static/css/output.old.css")

    static_path = os.path.join(STATIC_DIR, subfolder, file)
    if not os.path.exists(static_path):
        raise HTTPException(404, "File not found")

    return FileResponse(static_path)


async def index():
    async with aiofiles.open("./selected-media.json", "r", encoding="utf8") as f:
        selected_media = json.loads(await f.read())

    movie_tasks = []
    for movie_id in selected_media["movies"]:
        movie_tasks.append(imdb.get_media(movie_id, "pt"))

    series_tasks = []
    for series_id in selected_media["series"]:
        series_tasks.append(imdb.get_media(series_id, "pt"))

    tasks = [
        asyncio.gather(*movie_tasks),
        asyncio.gather(*series_tasks),
    ]
    selected_movies, selected_series = await asyncio.gather(*tasks)

    # render template
    data = {
        "selected_movies": selected_movies,
        "selected_series": selected_series,
    }
    template = templates.get_template("index.html")
    return HTMLResponse(template.render(data))


async def redirect(url: str):
    template = templates.get_template("loading.html")
    data = {"next_url": url}
    return HTMLResponse(template.render(data))


async def movie_info(id: str):
    tasks = [
        imdb.get_media(id, "pt"),
        imdb.get_related_media(id, "pt"),
    ]
    info, related = await asyncio.gather(*tasks)

    # render template
    template = templates.get_template("movie.html")
    data = {
        "info": info,
        "related_media": related,
    }
    return HTMLResponse(template.render(data))


async def series_info(id: str, season: int):
    tasks = [
        imdb.get_media(id, "pt"),
        imdb.get_related_media(id, "pt"),
    ]
    info, related = await asyncio.gather(*tasks)

    # get total season count
    season_count = 1
    for episode in info.episodes:
        if episode.season > season_count:
            season_count = episode.season

    # render template
    template = templates.get_template("series.html")
    data = {
        "info": info,
        "related_media": related,
        "current_season": season,
        "season_count": range(1, season_count + 1),
    }
    return HTMLResponse(template.render(data))


async def watch_movie(id: str, proxy_url: str):
    # run scrapers
    tasks = [
        pobreflix.movie_streams(id, proxy_url=proxy_url),
        static_sources.movie_streams(id, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    # get stream or return 404 error
    try:
        stream = streams[0].url
    except IndexError:
        raise HTTPException(404, "Stream not found")

    # render player template
    template = templates.get_template("player.html")
    data = {"url": stream}
    return HTMLResponse(template.render(data))


async def watch_series(id: str, season: int, episode: int, proxy_url: str):
    series_data = await imdb.get_media(id, "pt")

    # get url of the next episode
    next_url = f"/watch/series/{id}/1/1"
    found_cur_ep = False
    for episode_data in series_data.episodes:  # type: ignore
        # check if the current episode has been found on the list of episodes
        if episode_data.season == season and episode_data.episode == episode:
            found_cur_ep = True
            continue

        # get the url right after the current episode
        if found_cur_ep:
            next_url = f"/watch/series/{id}/{episode_data.season}/{episode_data.episode}"
            break

    # run scrapers
    tasks = [
        pobreflix.series_stream(id, season, episode, proxy_url=proxy_url),
        static_sources.series_stream(id, season, episode, proxy_url=proxy_url),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    # get stream or redirect to next episode if none is found
    try:
        stream = streams[0].url
    except IndexError:
        logger.error("Episode stream not found, redirecting to next episode...")
        return RedirectResponse(next_url)

    # render player template
    template = templates.get_template("player.html")
    data = {"url": stream, "next_url": f"/redirect/?url={next_url}"}
    return HTMLResponse(template.render(data))


async def search(term: str):
    results = await imdb.search(term, "pt")

    template = templates.get_template("search.html")
    data = {"results": results}
    return HTMLResponse(template.render(data))
