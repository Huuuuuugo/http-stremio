# functions to get stremio formated streams for movies and series

from urllib.parse import urlencode

from src.utils.stremio import StremioStream, StremioStreamManager
from .main import get_media_pages, get_sources, get_epiosode_url
from .sources import streamtape_stream

ALLOWED_HOSTS = [
    "streamtape.com",
]

ALLOWED_REGEXS = []


async def movie_streams(imdb_id: str, proxy_url: str | None = None):
    try:
        pages = await get_media_pages(imdb_id)

        streams = StremioStreamManager()
        if "dub" in pages.keys():
            # get list of links to every avaliable source
            dub_sources = await get_sources(f"{pages['dub']}?area=online")

            # extract stream links from every source
            try:
                stream = await streamtape_stream(dub_sources["streamtape"])

                if proxy_url is None:
                    stream = StremioStream(stream.url, headers=stream.headers, name="Pobreflix", title="Streamtape (DUB)")
                    streams.append(stream)
                else:
                    query = urlencode({"url": stream.url, "headers": stream.headers})
                    stream = StremioStream(f"{proxy_url}?{query}", name="Pobreflix", title="Streamtape (DUB)")
                    streams.append(stream)
            except:
                pass

        if "leg" in pages.keys():
            # get list of links to every avaliable source
            leg_sources = await get_sources(f"{pages['leg']}?area=online")

            # extract stream links from every source
            try:
                stream = await streamtape_stream(leg_sources["streamtape"])

                if proxy_url is None:
                    stream = StremioStream(stream.url, headers=stream.headers, name="Pobreflix", title="Streamtape (LEG)")
                    streams.append(stream)
                else:
                    query = urlencode({"url": stream.url, "headers": stream.headers})
                    stream = StremioStream(f"{proxy_url}?{query}", name="Pobreflix", title="Streamtape (LEG)")
                    streams.append(stream)
            except:
                pass

        # format as a stremio json
        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in pobreflix scraper! {e.__class__.__name__}: {e}")
        return []


async def series_stream(imdb_id: str, season: int, episode: int, proxy_url: str | None = None):
    try:
        pages = await get_media_pages(imdb_id)

        streams = StremioStreamManager()
        if "dub" in pages.keys():
            # get list of links to every avaliable source
            episode_url = await get_epiosode_url(pages["dub"], season, episode)
            if episode_url is not None:
                dub_sources = await get_sources(episode_url)

                # extract stream links from every source
                try:
                    stream = await streamtape_stream(dub_sources["streamtape"])

                    if proxy_url is None:
                        stream = StremioStream(stream.url, stream.headers, name="Pobreflix", title="Streamtape (DUB)")
                        streams.append(stream)
                    else:
                        query = urlencode({"url": stream.url, "headers": stream.headers})
                        stream = StremioStream(f"{proxy_url}?{query}", name="Pobreflix", title="Streamtape (DUB)")
                        streams.append(stream)
                except:
                    pass

        if "leg" in pages.keys():
            # get list of links to every avaliable source
            episode_url = await get_epiosode_url(pages["leg"], season, episode)
            if episode_url is not None:
                leg_sources = await get_sources(episode_url)

                # extract stream links from every source
                try:
                    stream = await streamtape_stream(leg_sources["streamtape"])

                    if proxy_url is None:
                        stream = StremioStream(stream.url, stream.headers, name="Pobreflix", title="Streamtape (LEG)")
                        streams.append(stream)
                    else:
                        query = urlencode({"url": stream.url, "headers": stream.headers})
                        stream = StremioStream(f"{proxy_url}?{query}", name="Pobreflix", title="Streamtape (LEG)")
                        streams.append(stream)
                except:
                    pass

        return streams.to_list()

    except Exception as e:
        print(f"Exception raised in pobreflix scraper! {e.__class__.__name__}: {e}")
        return []
