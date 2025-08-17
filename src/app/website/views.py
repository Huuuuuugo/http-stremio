from urllib.parse import urljoin, urlencode
import asyncio
import json
import os
import re

import aiohttp
import aiofiles
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from src.app import config
from src.scrapers import redecanais, pobreflix
from .constants import TEMPLATES_DIR, STATIC_DIR

templates = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


async def static(subfolder: str, file: str, user_agent: str = ""):
    # if the tailwind css output is requested, check the browser version
    # if the browser is too old, redirect to a compatible version of the css file
    if subfolder == "css" and file == "output.css":
        matches = re.findall(r"((?:Chrome)|(?:Firefox))/(\d+)\.", user_agent)
        print(matches)
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

    async with aiohttp.ClientSession() as session:
        # request info about each selected media
        movie_tasks = []
        for movie_id in selected_media["movies"]:
            url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/?id={movie_id}")
            if config.CACHE_URL:
                query = urlencode({"url": url})
                url = urljoin(config.CACHE_URL, f"?{query}")
            movie_tasks.append(session.get(url))

        series_tasks = []
        for series_id in selected_media["series"]:
            url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/?id={series_id}")
            if config.CACHE_URL:
                query = urlencode({"url": url})
                url = urljoin(config.CACHE_URL, f"?{query}")
            series_tasks.append(session.get(url))

        tasks = [
            asyncio.gather(*movie_tasks),
            asyncio.gather(*series_tasks),
        ]
        movie_tasks, series_tasks = await asyncio.gather(*tasks)

        # turn every response into a dict
        movie_tasks = [task.json() for task in movie_tasks]
        series_tasks = [task.json() for task in series_tasks]
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
    # mount url for getting the movie info
    info_url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/?id={id}")
    if config.CACHE_URL:
        query = urlencode({"url": info_url})
        info_url = urljoin(config.CACHE_URL, f"?{query}")

    # mount url for getting media related to the movie
    related_url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/related-media/?id={id}")
    if config.CACHE_URL:
        query = urlencode({"url": related_url})
        related_url = urljoin(config.CACHE_URL, f"?{query}")

    # make requests and format responses
    async with aiohttp.ClientSession() as session:
        # make requests
        tasks = [
            session.get(info_url),
            session.get(related_url),
        ]
        info, related = await asyncio.gather(*tasks)

        # turn results into dicts
        tasks = [
            info.json(),
            related.json(),
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
    # mount url for getting the series info
    info_url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/?id={id}")
    if config.CACHE_URL:
        query = urlencode({"url": info_url})
        info_url = urljoin(config.CACHE_URL, f"?{query}")

    # mount url for getting media related to the movie
    related_url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/imdb/related-media/?id={id}")
    if config.CACHE_URL:
        query = urlencode({"url": related_url})
        related_url = urljoin(config.CACHE_URL, f"?{query}")

    # make requests and format responses
    async with aiohttp.ClientSession() as session:
        # make requests
        tasks = [
            session.get(info_url),
            session.get(related_url),
        ]
        info, related = await asyncio.gather(*tasks)

        # turn results into dicts
        tasks = [
            info.json(),
            related.json(),
        ]
        info, related = await asyncio.gather(*tasks)

    # get total season count
    season_count = 1
    for episode in info["episodes"]:
        if episode["season"] > season_count:
            season_count = episode["season"]

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
        pobreflix.movie_streams(id, proxy_url=proxy_url, cache_url=config.CACHE_URL),
        redecanais.movie_streams(id, proxy_url=proxy_url, cache_url=config.CACHE_URL),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    # get stream or return 404 error
    try:
        stream = streams[0]["url"]
    except IndexError:
        raise HTTPException(404, "Stream not found")

    # render player template
    template = templates.get_template("player.html")
    data = {"url": stream}
    return HTMLResponse(template.render(data))


async def watch_series(id: str, season: int, episode: int, proxy_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://v3-cinemeta.strem.io/meta/series/{id}.json") as response:
            series_data = await response.json()

    # get url of the next episode
    next_url = f"/watch/series/{id}/1/1"
    found_cur_ep = False
    for ep_dict in series_data["meta"]["videos"]:
        # check if the current episode has been found on the list of episodes
        if ep_dict["season"] == season and ep_dict["number"] == episode:
            found_cur_ep = True
            continue

        # get the url right after the current episode
        if found_cur_ep:
            next_url = f"/watch/series/{id}/{ep_dict['season']}/{ep_dict['number']}"
            break

    # run scrapers
    tasks = [
        pobreflix.series_stream(id, season, episode, proxy_url=proxy_url, cache_url=config.CACHE_URL),
        redecanais.series_stream(id, season, episode, proxy_url=proxy_url, cache_url=config.CACHE_URL),
    ]
    results = await asyncio.gather(*tasks)
    streams = []
    for result in results:
        streams += result

    # get stream or redirect to next episode if none is found
    try:
        stream = streams[0]["url"]
    except IndexError:
        print("Episode stream not found, redirecting to next episode...")
        return RedirectResponse(next_url)

    # render player template
    template = templates.get_template("player.html")
    data = {"url": stream, "next_url": f"/redirect/?url={next_url}"}
    return HTMLResponse(template.render(data))


async def search(term: str):
    search_url = urljoin(config.LOCAL_ADDRESS, f"/info/pt/search/?term={term}")
    if config.CACHE_URL:
        query = urlencode({"url": search_url})
        search_url = urljoin(config.CACHE_URL, f"?{query}")
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as res:
            results = await res.json()

    template = templates.get_template("search.html")
    data = {"results": results}
    return HTMLResponse(template.render(data))
