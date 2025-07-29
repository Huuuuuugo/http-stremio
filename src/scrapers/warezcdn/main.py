from urllib.parse import urljoin
import typing
import json
import re

import aiohttp

from .exceptions import *

EMBED_URL = "https://embed.warezcdn.link"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"


class AudioData(typing.TypedDict):
    id: str
    audio: str
    servers: str


async def get_movie_audios(imdb_id: str) -> list[AudioData]:
    async with aiohttp.ClientSession() as session:
        movie_page_url = urljoin(EMBED_URL, f"/filme/{imdb_id}")
        async with session.get(movie_page_url) as movie_page:
            audio_data_matches = re.findall(r"let data = (?:\'|\")(.+)(?:\'|\")", await movie_page.text())
            if audio_data_matches:
                audio_data = json.loads(audio_data_matches[0])
                return audio_data
            else:
                msg = "Could not extract audio data from the movie page HTML"
                raise MovieHTMLParsingError(msg)


async def get_series_audios(imdb_id: str, season: int, episode: int) -> list[AudioData]:
    async with aiohttp.ClientSession() as session:
        # get series page and url to season info json
        series_page_url = urljoin(EMBED_URL, f"/serie/{imdb_id}")
        async with session.get(series_page_url) as series_page:
            seasons_url_matches = re.findall(r"var cachedSeasons = (?:\'|\")(.+)(?:\'|\")", await series_page.text())
            if seasons_url_matches:
                seasons_url = urljoin(EMBED_URL, seasons_url_matches[0])
            else:
                msg = "Could not extract seasons info url from series page HTML"
                raise SeriesHTMLParsingError(msg)

        # get seasons info json
        async with session.get(seasons_url) as seasons_response:
            seasons_json = json.loads(await seasons_response.text())

        # get target season
        seasons_json = seasons_json["seasons"]
        target_season_id = list(seasons_json.keys())[season - 1]
        target_season_json = seasons_json[target_season_id]

        # get target episode
        episodes_json = target_season_json["episodes"]
        for key in episodes_json.keys():
            if int(episodes_json[key]["name"]) == episode:
                target_episode_json = episodes_json[key]

        # get audio data for the target episode
        episode_audios_url = urljoin(EMBED_URL, f"/core/ajax.php?audios={target_episode_json['id']}")
        async with session.get(episode_audios_url, headers={"referer": series_page_url}) as episode_audios_response:
            content = re.sub(r"\\", "", await episode_audios_response.text())
            content = re.findall(r"\"(.+)\"", content)[0]
            audio_data = json.loads(content)

            return audio_data
