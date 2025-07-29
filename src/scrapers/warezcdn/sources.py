from urllib.parse import urljoin
import typing
import json
import re

import aiohttp

from src.utils.stremio import StremioStream
from .main import EMBED_URL, USER_AGENT, AudioData


class WarezcdnStream:
    @classmethod
    async def get_video_url(
        cls,
        imdb_id: str,
        type: typing.Literal["filme", "serie"],
        audio_data: AudioData,
    ) -> str:
        async with aiohttp.ClientSession() as session:
            # reused values
            id = audio_data["id"]
            lang = audio_data["audio"]
            server = "warezcdn"

            # relevant urls
            media_page_url = urljoin(EMBED_URL, f"{type}/{imdb_id}")
            embed_video_url = urljoin(EMBED_URL, f"getEmbed.php?id={id}&sv={server}&lang={lang}")
            play_url = urljoin(EMBED_URL, f"/getPlay.php?id={id}&sv={server}")

            # get referer to avoid bot detection
            async with session.get(media_page_url, headers={"user-agent": USER_AGENT}) as response:
                await response.text()

            async with session.get(embed_video_url, headers={"referer": media_page_url, "user-agent": USER_AGENT}) as response:
                await response.text()

            # get video url
            async with session.get(play_url, headers={"referer": embed_video_url, "host": "embed.warezcdn.link", "user-agent": USER_AGENT}) as play_response:
                video_url_matches = re.findall(r"window.location.href = (?:\'|\")(.+)(?:\'|\")", await play_response.text())
                if video_url_matches:
                    video_url = video_url_matches[0]
                    return video_url

    @classmethod
    async def get_stream(cls, video_url: str) -> StremioStream:
        async with aiohttp.ClientSession() as session:
            # exctract relevant information from stream
            video_host_url = re.findall(r"(https://.+?)/", video_url)[0]
            video_hash = re.findall(r"/([\w]+?)(?:$|\?)", video_url)[0]

            # get video url to avoid bot detection
            async with session.get(video_url) as response:
                await response.text()

            # get player info json that contains the master.m3u8 url
            player_info_url = urljoin(video_host_url, f"/player/index.php?data={video_hash}&do=getVideo")
            data = {"hash": video_hash, "r": ""}
            headers = {
                "x-requested-with": "XMLHttpRequest",
                "referer": EMBED_URL,
                "user-agent": USER_AGENT,
            }
            async with session.post(player_info_url, data=data, headers=headers) as player_info_response:
                player_info_json = json.loads(await player_info_response.text())
                master_m3u8_url = player_info_json["securedLink"]

            # get video m3u8 url
            async with session.get(master_m3u8_url) as master_m3u8_response:
                master_m3u8 = await master_m3u8_response.text()
                for line in master_m3u8.split("\n"):
                    matches = re.match(r"https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})(:\d+)?(/[^\s]*)?", line)
                    if matches:
                        stream_url = matches[0]
                        break

            return StremioStream(stream_url, headers={"origin": "https://basseqwevewcewcewecwcw.xyz"})

    @classmethod
    async def get(
        cls,
        imdb_id: str,
        type: typing.Literal["filme", "serie"],
        audio_data: AudioData,
    ) -> StremioStream:
        video_url = await cls.get_video_url(imdb_id, type, audio_data)
        stream_info = await cls.get_stream(video_url)

        name = "Warezcdn"
        title = f"Warezcdn ({'LEG' if audio_data["audio"] == '1' else 'DUB'})"
        return StremioStream(stream_info.url, headers=stream_info.headers, name=name, title=title)


async def warezcdn_stream(
    imdb_id: str,
    type: typing.Literal["filme", "serie"],
    audio_data: AudioData,
) -> StremioStream:
    return await WarezcdnStream.get(imdb_id, type, audio_data)
