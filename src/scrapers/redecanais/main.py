# general functions and classes needed to scrape the site

from urllib.parse import urljoin, quote_plus, urlencode
import json
import re
import os

from bs4 import BeautifulSoup
import aiohttp

from src.utils import imdb
from .sources import REDECANAIS_URL
from .utils import to_kebab_case
from .decoders import decode_from_response

# dict containg links to all movies grouped by first letter
MOVIE_LIST = {}

# media where the imdb title doesn't match the one on the site
# also used for caching
module_path = os.path.dirname(__file__)
with open(os.path.join(module_path, "data/movies.json"), "r", encoding="utf8") as f:
    MOVIES_JSON: dict = json.loads(f.read())

with open(os.path.join(module_path, "data/series.json"), "r", encoding="utf8") as f:
    SERIES_JSON: dict = json.loads(f.read())

# add individual json files from data/series to SERIES_JSON
series_jsons_folder = os.path.join(module_path, "data/series")
series_jsons_list = os.listdir(series_jsons_folder)
for file in series_jsons_list:
    with open(os.path.join(series_jsons_folder, file)) as f:
        json_data = json.loads(f.read())
        SERIES_JSON.update(json_data)


async def parse_movie_list():
    """Turn list of movies and list of series into dicts grouped by initial letters"""
    print("parse_media_lists")
    async with aiohttp.ClientSession() as session:
        async with session.get(urljoin(REDECANAIS_URL, "final_mapafilmes.txt")) as movie_list_response:
            # iterate through every line of movies html searching for urls
            list_started = False
            movie_list_text = await movie_list_response.text()
            for line in movie_list_text.split("\n"):
                line = str(line)
                # wait for the beggining of the list to be reached
                if not list_started:
                    if "<b>Filmes</b>" in line:
                        list_started = True

                else:
                    url = re.findall(r"href *= *\"(.+?)\"", line)
                    if url:
                        url = url[0]

                        # append url to the list corresponding to its first letter
                        first_letter = url[1]
                        if first_letter.isalpha():
                            try:
                                MOVIE_LIST[first_letter].append(url)
                            except KeyError:
                                MOVIE_LIST.update({first_letter: []})
                                MOVIE_LIST[first_letter].append(url)
                        else:
                            try:
                                MOVIE_LIST["-"].append(url)
                            except KeyError:
                                MOVIE_LIST.update({"-": []})
                                MOVIE_LIST["-"].append(url)


async def find_episode_pages(series_page_url: str, season: int, episode: int, cache_url: None | str = None) -> dict:
    if cache_url:
        query = urlencode({"url": series_page_url})
        series_page_url = f"{cache_url}?{query}"

    async with aiohttp.ClientSession() as session:
        async with session.get(series_page_url) as response:
            html = BeautifulSoup(await decode_from_response(response), "html.parser")

    # get the html element containing all episodes
    p_list = html.find_all("p")
    episodes_html = ""
    for p in p_list:
        p: BeautifulSoup
        if len(p.text) > len(episodes_html):
            episodes_html = p.prettify()

    # search for the season and episode sequentially
    season_found = False
    episode_found = False
    episode_urls = []
    episode_audios = []
    episode_pages = {}
    curr_episode_number = 1
    for line in episodes_html.splitlines():
        # search for the target season
        if not season_found:
            if "Temporada" in line and str(season) in line:
                season_found = True
                continue

        # search for the target episode
        elif not episode_found:
            if "Episódio" in line:
                if curr_episode_number == episode:
                    episode_found = True
                    continue
                curr_episode_number += 1

        # search for the episode pages urls
        else:
            url = re.findall(r"href *= *\"(.+?)\"", line)
            if url:
                url = urljoin(REDECANAIS_URL, url[0])
                episode_urls.append(url)

            # mark episode as dub or leg
            elif "Legendado" in line:
                episode_audios.append("leg")
            elif "Assistir" in line or "Dublado" in line:
                episode_audios.append("dub")

            # break loop if a new episode or season or the max amount of streams is reached
            elif "Ep" in line and str(episode + 1) in line:
                break
            elif "Temporada" in line and str(season + 1) in line:
                break
            if len(episode_urls) >= 2:
                break

    # mount the pages dict
    for i, key in enumerate(episode_audios):
        episode_pages.update({key: episode_urls[i]})

    return episode_pages


async def get_series_pages(imdb_id: str, season: int, episode: int, cache_url: None | str = None):
    # check if the episode page url is inside series.json
    try:
        episode_pages = SERIES_JSON[imdb_id]["seasons"][str(season)]["episodes"][str(episode)]
        print(episode_pages)
        for key in episode_pages:
            url = episode_pages[key]
            url = urljoin(REDECANAIS_URL, url)
            episode_pages[key] = url

    except KeyError:
        # check if te series page url is inside series.json
        try:
            page_url = SERIES_JSON[imdb_id]["page_url"]

        except KeyError:
            print("get_series_pages")
            info = await imdb.get_media(imdb_id, "pt", cache_url)
            title = to_kebab_case(info.title)

            # format video page url using the redecanais pattern
            page_url = f"/browse-{title}-videos-1-date.html"

        page_url = urljoin(REDECANAIS_URL, page_url)
        episode_pages = await find_episode_pages(page_url, season, episode, cache_url)

    return episode_pages


async def get_movie_pages(imdb_id: str, cache_url: None | str) -> dict:
    try:
        media_pages = MOVIES_JSON[imdb_id]
        media_pages = {key: urljoin(REDECANAIS_URL, media_pages[key]) for key in media_pages.keys()}

    except KeyError:
        # get information about the target media
        info = await imdb.get_media(imdb_id, "pt", cache_url)
        title = to_kebab_case(info.title)
        year = str(info.year)
        first_char = title[0] if title[0].isalpha() else "-"

        # parse lists used on the search if not parsed yet
        if not MOVIE_LIST:
            await parse_movie_list()

        # search for the target media
        media_pages = {}
        for url in MOVIE_LIST[first_char]:
            if title in url and year in url:
                if "legendado" in url:
                    media_pages.update({"leg": urljoin(REDECANAIS_URL, url)})
                else:
                    media_pages.update({"dub": urljoin(REDECANAIS_URL, url)})

                MOVIE_LIST.update({imdb_id: media_pages})

    return media_pages
