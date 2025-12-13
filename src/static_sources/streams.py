from urllib.parse import urlencode

from src.utils.stremio import StremioStream, StremioStreamManager
from .schemas import MovieSourceRead, SeriesSourceRead
from .services import StaticSourceService
from .db import SessionLocal

ALLOWED_HOSTS = [
    "archive.org",
]

ALLOWED_REGEXS = []


async def movie_streams(imdb_id: str, proxy_url: str | None = None):
    try:
        streams = StremioStreamManager()

        async with SessionLocal() as db:
            service = StaticSourceService(db)

            results = await service.read(MovieSourceRead(code=imdb_id))
            for stream in results:
                # extract stream links from every source
                try:
                    if proxy_url is None:
                        stream = StremioStream(stream.url, headers=stream.headers, name="Static Sources", title=stream.title)
                        streams.append(stream)
                    else:
                        query = urlencode({"url": stream.url, "headers": stream.headers})
                        stream = StremioStream(f"{proxy_url}?{query}", name="Static Sources", title=stream.title)
                        streams.append(stream)
                except:
                    pass

        # format as a stremio json
        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in static_sources module! {e.__class__.__name__}: {e}")
        return []


async def series_stream(imdb_id: str, season: int, episode: int, proxy_url: str | None = None):
    try:
        streams = StremioStreamManager()

        async with SessionLocal() as db:
            service = StaticSourceService(db)

            results = await service.read(SeriesSourceRead(code=imdb_id, season=season, episode=episode))
            for stream in results:
                # extract stream links from every source
                try:
                    if proxy_url is None:
                        stream = StremioStream(stream.url, headers=stream.headers, name="Static Sources", title=stream.title)
                        streams.append(stream)
                    else:
                        query = urlencode({"url": stream.url, "headers": stream.headers})
                        stream = StremioStream(f"{proxy_url}?{query}", name="Static Sources", title=stream.title)
                        streams.append(stream)
                except:
                    pass

        # format as a stremio json
        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in static_sources module! {e.__class__.__name__}: {e}")
        return []
