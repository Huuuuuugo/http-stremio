import time
import asyncio
from collections import OrderedDict, namedtuple
import aiohttp
from src.utils.stremio import StremioStream
from urllib.parse import urlparse, parse_qs


BLOCKED_SOURCES = ["static_sources"]


class StreamCache:
    def __init__(self, max_size=1024):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.enable = True
        self.expiry_margin = 300  # 5 minutes

    async def _test(self, url: str, headers: dict) -> bool:
        test_url = url
        test_headers = headers

        # excract url
        if "/proxy/stream/" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if "url" in query_params:
                test_url = query_params["url"][0]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    test_url, headers=test_headers, allow_redirects=True, timeout=5
                ) as response:
                    if 199 < response.status < 400:
                        return True
                    return False
        except:
            return False

    async def get(self, imdb_id: str) -> tuple[list[StremioStream], list[str]]:
        if not self.enable:
            return [], []

        cached_items = self.cache.get(imdb_id)
        if not cached_items:
            return [], []

        valid_streams = []
        invalid_sources = set()

        tasks = []
        stream_map = {}
        # invalidate expired and invalid sources before test them
        for item in cached_items:
            if item.source in invalid_sources:
                continue
            if (
                time.time() + 600
                >= item.expiry  # TODO: choose a better margin but for tests thats ok
            ):  # prevent the link from becoming invalid during streaming
                invalid_sources.add(item.source)
                continue
            if item.duration and (item.expiry - self.expiry_margin) < (
                time.time() + item.duration
            ):  # prevent the invalid more precisely
                invalid_sources.add(item.source)
                continue

            task = asyncio.create_task(self._test(item.url, item.headers))
            tasks.append(task)
            stream_map[task] = item

        # test the validated streams
        test_results = await asyncio.gather(*tasks)

        for task, is_valid in zip(tasks, test_results):
            stream = stream_map[task]
            if is_valid:
                valid_streams.append(stream)
            else:
                invalid_sources.add(stream.source)

        if valid_streams:
            self.cache.move_to_end(imdb_id)

        return valid_streams, list(invalid_sources)

    def set(self, imdb_id: str, value: list[StremioStream]):
        if not self.enable:
            return

        if len(self.cache) >= self.max_size and imdb_id not in self.cache:
            self.cache.popitem(last=False)

        new_cached_streams = []
        for stream in value:
            if stream.expiry is None:
                stream.expiry = int(time.time()+3600)
            source = getattr(stream, "source")
            if source not in BLOCKED_SOURCES:
                new_cached_streams.append(stream)

        if not new_cached_streams:
            return

        self.cache[imdb_id] = new_cached_streams


stream_cache = StreamCache(max_size=1024)
