# functions to get stremio formated streams for movies and series

from urllib.parse import urlencode

from utils.stremio import StremioStream, StremioStreamManager
from .main import get_movie_pages, get_series_pages
from .sources import player_stream, HOSTS


async def movie_streams(imdb: str, proxy_url: str | None = None, cache_url: None | str = None):
    try:
        pages = await get_movie_pages(imdb, cache_url)

        streams = StremioStreamManager()
        if "dub" in pages.keys():
            # get video stream
            stream = await player_stream(pages["dub"], cache_url)

            if proxy_url is None:
                # create formated stream json
                stream = StremioStream(stream.url, headers=stream.headers, name="Redecanais", title="Redecanais (DUB)")
                streams.append(stream)
            else:
                # create formated stream json using proxy
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name="Redecanais", title="Redecanais (DUB)")
                streams.append(stream)

        if "leg" in pages.keys():
            # get video stream
            stream = await player_stream(pages["leg"], cache_url)

            if proxy_url is None:
                # create formated stream json
                stream = StremioStream(stream.url, stream.headers, name="Redecanais", title="Redecanais (LEG)")
                streams.append(stream)

            else:
                # create formated stream json using proxy
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name="Redecanais", title="Redecanais (LEG)")
                streams.append(stream)

        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in redecanais scraper! {e.__class__.__name__}: {e}")
        return []


async def series_stream(imdb: str, season: int, episode: int, proxy_url: str | None = None, cache_url: None | str = None):
    try:
        pages = await get_series_pages(imdb, season, episode, cache_url)

        streams = StremioStreamManager()
        if "dub" in pages.keys():
            # get video stream
            stream = await player_stream(pages["dub"], cache_url)

            if proxy_url is None:
                # create formated stream json
                stream = StremioStream(stream.url, headers=stream.headers, name="Redecanais", title="Redecanais (DUB)")
                streams.append(stream)
            else:
                # create formated stream json using proxy
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name="Redecanais", title="Redecanais (DUB)")
                streams.append(stream)

        if "leg" in pages.keys():
            # get video stream
            stream = await player_stream(pages["leg"], cache_url)

            if proxy_url is None:
                # create formated stream json
                stream = StremioStream(stream.url, stream.headers, name="Redecanais", title="Redecanais (LEG)")
                streams.append(stream)

            else:
                # create formated stream json using proxy
                query = urlencode({"url": stream.url, "headers": stream.headers})
                stream = StremioStream(f"{proxy_url}?{query}", name="Redecanais", title="Redecanais (LEG)")
                streams.append(stream)

        return streams.to_list()

    except Exception as e:
        import traceback

        print(f"Exception raised in redecanais scraper! {e.__class__.__name__}: {e}")
        traceback.print_exc()
        return []
