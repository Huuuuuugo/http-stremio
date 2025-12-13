import os

from ...scrapers import pobreflix
from ... import static_sources

# conjunction of raw hosts strings defined here and on each scraper
ALLOWED_HOSTS = [
    "localhost",
    "www.imdb.com",
    "live.metahub.space",
    "m.media-amazon.com",
    "images.metahub.space",
    "v3-cinemeta.strem.io",
    "episodes.metahub.space",
    *pobreflix.ALLOWED_HOSTS,
    *static_sources.ALLOWED_HOSTS,
]

# list of regular expressions that match urls used by scrapers
ALLOWED_REGEXS = [
    *pobreflix.ALLOWED_REGEXS,
    *static_sources.ALLOWED_REGEXS,
]


HLS_CONTENT_TYPE_HEADERS = [
    "application/vnd.apple.mpegURL",
    "application/x-mpegURL",
    "audio/mpegurl",
    "audio/x-mpegurl",
    "text/plain",
]

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
MAX_CACHE_DIR_SIZE = 200 * 1024 * 1024  # 200 megabytes
