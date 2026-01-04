from urllib.parse import urlencode

from src.utils.stremio import StremioStream
from .schemas import MovieSourceRead, SeriesSourceRead
from .services import StaticSourceService
from .db import SessionLocal

ALLOWED_HOSTS = [
    "archive.org",
]

ALLOWED_REGEXS = []

SOURCE_NAME = "static_sources"


async def movie_streams(
    imdb_id: str, proxy_url: str | None = None
) -> list[StremioStream]:
    try:
        streams = []

        async with SessionLocal() as db:
            service = StaticSourceService(db)

            results = await service.read(MovieSourceRead(code=imdb_id))
            for stream in results:
                # extract stream links from every source
                try:
                    if proxy_url is None:
                        streams.append(
                            StremioStream(
                                stream.url,
                                headers=stream.headers,
                                name="Static Sources",
                                title=stream.title,
                                source=SOURCE_NAME,
                            )
                        )
                    else:
                        query = urlencode(
                            {"url": stream.url, "headers": stream.headers}
                        )
                        streams.append(
                            StremioStream(
                                f"{proxy_url}?{query}",
                                name="Static Sources",
                                title=stream.title,
                                source=SOURCE_NAME,
                            )
                        )
                except:
                    pass

        return streams

    except Exception as e:
        print(f"Exception raised in static_sources module! {e.__class__.__name__}: {e}")
        return []


async def series_stream(
    imdb_id: str, season: int, episode: int, proxy_url: str | None = None
) -> list[StremioStream]:
    try:
        streams = []

        async with SessionLocal() as db:
            service = StaticSourceService(db)

            results = await service.read(
                SeriesSourceRead(code=imdb_id, season=season, episode=episode)
            )
            for stream in results:
                # extract stream links from every source
                try:
                    if proxy_url is None:
                        streams.append(
                            StremioStream(
                                stream.url,
                                headers=stream.headers,
                                name="Static Sources",
                                title=stream.title,
                                source=SOURCE_NAME,
                            )
                        )
                    else:
                        query = urlencode(
                            {"url": stream.url, "headers": stream.headers}
                        )
                        streams.append(
                            StremioStream(
                                f"{proxy_url}?{query}",
                                name="Static Sources",
                                title=stream.title,
                                source=SOURCE_NAME, 
                            )
                        )
                except:
                    pass

        return streams

    except Exception as e:
        print(f"Exception raised in static_sources module! {e.__class__.__name__}: {e}")
        return []
