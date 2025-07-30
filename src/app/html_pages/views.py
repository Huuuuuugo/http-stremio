import json
import os

import aiohttp
import aiofiles
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from src.app import config
from src.utils import imdb
from src.scrapers import redecanais
from .constants import TEMPLATES_DIR, STATIC_DIR

templates = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


async def static(subfolder: str, file: str):
    static_path = os.path.join(STATIC_DIR, subfolder, file)
    if not os.path.exists(static_path):
        raise HTTPException(404, "File not found")

    return FileResponse(static_path)


async def index():
    async with aiofiles.open("./selected-media.json", "r", encoding="utf8") as f:
        selected_media = json.loads(await f.read())

    data = {
        "selected_movies": selected_media["movies"],
        "selected_series": selected_media["series"],
    }

    template = templates.get_template("index.html")
    return HTMLResponse(template.render(data))


async def redirect(url: str):
    template = templates.get_template("loading.html")
    data = {"next_url": url}
    return HTMLResponse(template.render(data))


async def movie_info(id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://v3-cinemeta.strem.io/meta/movie/{id}.json") as response:
            series_data = await response.json()

    # get movie variables
    name = series_data["meta"]["name"]
    background = series_data["meta"]["background"]
    poster = series_data["meta"]["poster"]
    logo = series_data["meta"]["logo"]

    # render template
    template = templates.get_template("movie.html")
    data = {
        "name": name,
        "logo": logo,
        "poster": poster,
        "background": background,
        "id": id,
    }
    return HTMLResponse(template.render(data))


async def series_info(id: str, season: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://v3-cinemeta.strem.io/meta/series/{id}.json") as response:
            series_data = await response.json()

    # create a dict for every season
    seasons = {}
    for video in series_data["meta"]["videos"]:
        if video["season"] == 0:
            continue

        episode = {}
        if video["season"] == season:
            episode = {
                "number": video["number"],
                "title": video["name"],
                "image": video["thumbnail"],
            }

        try:
            seasons[video["season"]]["episodes"].append(episode)

        except KeyError:
            seasons.update({video["season"]: {"number": video["season"], "episodes": []}})
            seasons[video["season"]]["episodes"].append(episode)

    # convert seasons dict to a list
    seasons = [seasons[key] for key in seasons.keys()]

    # get remaining series variables
    name = series_data["meta"]["name"]
    background = series_data["meta"]["background"]
    poster = series_data["meta"]["poster"]
    logo = series_data["meta"]["logo"]

    # render template
    template = templates.get_template("series.html")
    data = {
        "seasons": seasons,
        "curr_season": season,
        "name": name,
        "logo": logo,
        "poster": poster,
        "background": background,
        "id": id,
    }
    return HTMLResponse(template.render(data))


async def watch_movie(id: str, proxy_url: str):
    # get stream
    streams = await redecanais.movie_streams(id, proxy_url=proxy_url, cache_url=config.CACHE_URL)
    stream = streams[0]["url"]

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

    # get stream
    streams = await redecanais.series_stream(id, season, episode, proxy_url=proxy_url, cache_url=config.CACHE_URL)
    try:
        stream = streams[0]["url"]
    except IndexError:
        print("apisode stream not found, redirecting to next episode...")
        return RedirectResponse(next_url)

    # render player template
    template = templates.get_template("player.html")
    data = {"url": stream, "next_url": f"/redirect/?url={next_url}"}
    return HTMLResponse(template.render(data))
