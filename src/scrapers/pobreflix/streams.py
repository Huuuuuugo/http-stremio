# functions to get stremio formated streams for movies and series

from urllib.parse import urlencode

from src.utils.stremio import StremioStream
from .main import get_media_pages, get_sources, get_epiosode_url
from .sources import streamtape_stream

ALLOWED_HOSTS = [
    "streamtape.com",
]

ALLOWED_REGEXS = []

SOURCE_NAME = "pobreflix"


async def _get_streams(
    imdb_id: str,
    season: int | None = None,
    episode: int | None = None,
    proxy_url: str | None = None,
) -> StremioStream:
    pages = await get_media_pages(imdb_id)
    streams = []
    for page in pages:
        audio_type = getattr(page, "audio", None)
        page_url = getattr(page, "url", None)
        if audio_type in ["dub", "leg"] and page_url:
            try:
                if season is not None and episode is not None:
                    target_url = await get_epiosode_url(page_url, season, episode)
                else:
                    target_url = f"{page_url}?area=online"

                if not target_url:
                    continue

                sources = await get_sources(target_url)
                if "streamtape" not in sources:
                    continue

                stream_data = await streamtape_stream(sources["streamtape"])

                if proxy_url:
                    query = urlencode(
                        {"url": stream_data.url, "headers": stream_data.headers}
                    )
                    final_url = f"{proxy_url}?{query}"
                else:
                    final_url = stream_data.url
                streams.append(
                    StremioStream(
                        url=final_url,
                        headers=stream_data.headers,
                        name="Pobreflix",
                        title=f"Streamtape ({audio_type.upper()})",
                        source=SOURCE_NAME,
                        ttl=60000,
                    )
                )
            except Exception:
                continue

    return streams


async def movie_streams(
    imdb_id: str, proxy_url: str | None = None
) -> list[StremioStream]:
    try:
        streams = await _get_streams(imdb_id, proxy_url)
        return streams
    except Exception as e:
        print(f"Exception raised in pobreflix scraper! {e.__class__.__name__}: {e}")
        return []


async def series_stream(
    imdb_id: str, season: int, episode: int, proxy_url: str | None = None
) -> list[StremioStream]:
    try:
        streams = await _get_streams(imdb_id, season, episode, proxy_url)
        return streams
    except Exception as e:
        print(f"Exception raised in pobreflix scraper! {e.__class__.__name__}: {e}")
        return []
