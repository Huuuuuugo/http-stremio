# functions to extract stream links from site sources

from urllib.parse import urlencode, parse_qs, urljoin
import re

from bs4 import BeautifulSoup
import aiohttp

from src.utils.stremio import StremioStream
from .decoders import decode_from_text, decode_videojs
from .exceptions import *

REDECANAIS_URL = "https://redecanais.ee/"


class PlayerStream:
    @classmethod
    async def get_video_player_url(cls, video_page_url: str, cache_url: None | str = None) -> str:
        """Extract video player url from a given video page, such as the page for a movie or a specific episode of a series"""
        print("get_video_player_url")
        # get video page
        if cache_url:
            query = urlencode({"url": video_page_url, "expires": "4h"})
            video_page_url = f"{cache_url}?{query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(video_page_url) as video_page_response:
                text = await video_page_response.text()
                decoded_html = decode_from_text(text, 1)
                if not (200 <= video_page_response.status <= 299):
                    msg = f"Unexpected status code when requesting video page '{video_page_response.status}'"
                    raise UnexpectedStatusCode(msg)

                video_page_html = BeautifulSoup(decoded_html, "html.parser")

            # get video url
            player_url = ""
            for iframe in video_page_html.find_all("iframe"):
                name = iframe.get("name")
                if name is not None and name == "Player":
                    player_url = iframe.get("src")
                    player_url = urljoin(REDECANAIS_URL, player_url)

            print(player_url)

            if player_url:
                return player_url
            else:
                msg = "Failed to extract video player url from video page"
                raise VideoPageParsningError(msg)

    @classmethod
    async def get_videosjs_url(cls, video_player_url: str, cache_url: None | str = None) -> str:
        print("get_videojs_url")
        if cache_url:
            query = urlencode({"url": video_player_url, "expires": "4h"})
            video_player_url = f"{cache_url}?{query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(video_player_url) as video_player_response:
                text = await video_player_response.text()
                decoded_html = decode_from_text(text, 0)
                if not (200 <= video_player_response.status <= 299):
                    msg = f"Unexpected status code when requesting video page '{video_player_response.status}'"
                    raise UnexpectedStatusCode(msg)

                html = BeautifulSoup(decoded_html, "html.parser")

            # extract videojs url from video player html
            scripts = html.find_all("script")
            for script in scripts:
                # find script containing the videojs url
                if "VkFfQlVTQ0FSX0VNX09VVFJPX0xVR0FSX0hF" in script.text:
                    # ignore portion after the url strings
                    text = script.text.split(";")[0]

                    # ignore + and " chars
                    videojs_url = "".join(re.findall(r"\"([^\+\"]+?)\"", text))
                    videojs_url = urljoin(REDECANAIS_URL, videojs_url)
                    print(videojs_url)

                    return videojs_url

            msg = "Failed to extract videojs url from video player page"
            raise VideoPlayerParsningError(msg)

    @classmethod
    async def get_stream_url(cls, videojs_url: str, cache_url: None | str = None):
        print("get_stream_url")
        videojs_headers = {
            "x-requested-with": "RC-Site-Requests",
            "h31ffadrg3bb7": "h31ffadrg3fj345a",
        }

        if cache_url:
            query = urlencode({"url": videojs_url, "headers": videojs_headers, "expires": "4h"})
            videojs_url = f"{cache_url}?{query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(videojs_url, headers=videojs_headers) as videojs_response:
                text = await videojs_response.text()
                decoded_text = decode_videojs(text)

            urls = re.findall(r"(?:\"(?:https?:)?(//.+?)\")", decoded_text)
            urls = ["https:" + url for url in urls]

            expected_params = ["sv", "cc", "nu3zAQc9HC3GbwJq"]
            for url in urls:
                try:
                    query_params = url.split("?")[1]
                    query_params = parse_qs(query_params)
                except IndexError:
                    continue

                query_params = list(query_params)
                if query_params == expected_params:
                    print(url)
                    return url

    @classmethod
    async def get(cls, video_page_url: str, cache_url: None | str = None):
        print("get")
        print(video_page_url)
        video_player_url = await cls.get_video_player_url(video_page_url, cache_url)
        videojs_url = await cls.get_videosjs_url(video_player_url, cache_url)
        stream = await cls.get_stream_url(videojs_url, cache_url)

        headers = {
            "referer": REDECANAIS_URL,
        }

        return StremioStream(stream, headers=headers)


async def player_stream(video_page_url: str, cache_url: None | str = None) -> StremioStream:
    return await PlayerStream.get(video_page_url, cache_url)
