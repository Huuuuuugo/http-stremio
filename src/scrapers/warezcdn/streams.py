from urllib.parse import urlencode
import asyncio

from src.utils.stremio import StremioStream, StremioStreamManager
from .main import get_movie_audios, get_series_audios
from .sources import warezcdn_stream

ALLOWED_HOSTS = [
    "basseqwevewcewcewecwcw.xyz",
]

ALLOWED_REGEXS = [
    r"^https?://[a-z]+\.xyz/cdn/down/[a-z0-9]+/Video/[0-9]{3,4}p/.+$",
]


async def movie_streams(imdb_id: str, proxy_url: str | None = None):
    try:
        audio_list = await get_movie_audios(imdb_id)
        tasks = []
        for audio in audio_list:
            for server in audio["servers"].split(","):
                if server == "mixdrop":
                    continue
                if server == "warezcdn":
                    tasks.append(warezcdn_stream(imdb_id, "filme", audio))

        stream_info_list: list[StremioStream] = await asyncio.gather(*tasks)

        streams = StremioStreamManager()
        if proxy_url is None:
            for stream in stream_info_list:
                streams.append(stream)
        else:
            for stream in stream_info_list:
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name=stream.name, title=stream.title)
                streams.append(stream)

        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in warezcdn scraper! {e.__class__.__name__}: {e}")
        return []


async def series_stream(imdb_id: str, season: int, episode: int, proxy_url: str | None = None):
    try:
        audio_list = await get_series_audios(imdb_id, season, episode)
        tasks = []
        for audio in audio_list:
            for server in audio["servers"].split(","):
                if server == "mixdrop":
                    continue
                if server == "warezcdn":
                    tasks.append(warezcdn_stream(imdb_id, "filme", audio))

        stream_info_list: list[StremioStream] = await asyncio.gather(*tasks)

        streams = StremioStreamManager()
        if proxy_url is None:
            for stream in stream_info_list:
                streams.append(stream)
        else:
            for stream in stream_info_list:
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name=stream.name, title=stream.title)
                streams.append(stream)

        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in warezcdn scraper! {e.__class__.__name__}: {e}")
        return []
