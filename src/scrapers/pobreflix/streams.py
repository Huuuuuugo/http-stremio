# functions to get stremio formated streams for movies and series

from urllib.parse import parse_qs, urlencode, urlparse
import logging
from src.utils.stremio import StremioStream
from .main import get_media_pages, get_sources, get_epiosode_url
from .sources import streamtape_stream

ALLOWED_HOSTS = [
    "streamtape.com",
]

ALLOWED_REGEXS = []

SOURCE_NAME = "pobreflix"

logger = logging.getLogger(__name__)


async def _get_streams(
    imdb_id: str,
    season: int | None = None,
    episode: int | None = None,
    proxy_url: str | None = None,
) -> StremioStream:
    streams = []
    try:
        pages = await get_media_pages(imdb_id)
        for page in pages:
            audio_type = getattr(page, "audio", None)
            page_url = getattr(page, "url", None)
            if audio_type in ["dub", "leg"] and page_url:
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
                    query = urlencode({"url": stream_data.url, "headers": stream_data.headers})
                    final_url = f"{proxy_url}?{query}"
                else:
                    final_url = stream_data.url
                query_params = parse_qs(urlparse(stream_data.url).query)
                expires_value = query_params.get("expires", [None])[0]
                if expires_value and str(expires_value).isdigit():
                    expiry = int(expires_value)
                else:
                    expiry = None
                streams.append(
                    StremioStream(
                        url=final_url,
                        headers=stream_data.headers,
                        name="Pobreflix",
                        title=f"Streamtape ({audio_type.upper()})",
                        source=SOURCE_NAME,
                        expiry=expiry,
                    )
                )
    except Exception as e:
        logger.error(f"Exception raised in pobreflix scraper! {e.__class__.__name__}: {e}")
        pass

    return streams


async def movie_streams(imdb_id: str, proxy_url: str | None = None) -> list[StremioStream]:
    streams = await _get_streams(imdb_id, proxy_url=proxy_url)
    return streams


async def series_stream(imdb_id: str, season: int, episode: int, proxy_url: str | None = None) -> list[StremioStream]:
    streams = await _get_streams(imdb_id, season, episode, proxy_url)
    return streams
