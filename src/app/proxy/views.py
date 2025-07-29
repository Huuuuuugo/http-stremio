from urllib.parse import urlparse
import asyncio
import ast
import os

import aiohttp
from fastapi import Request
from fastapi.responses import StreamingResponse, FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import check_allowed_urls, add_proxy_to_hls_parts, yield_chunks
from .services import CacheMetaService, CacheMetaServiceExceptions
from .tasks import delete_exceeding_caches
from .constants import CACHE_DIR, HLS_CONTENT_TYPE_HEADERS

cache_proxy_lock = asyncio.Lock()


async def stream_proxy(request: Request, url: str, headers: dict, request_headers: dict):
    # check if the url host is on the allow list
    check_allowed_urls(url)

    # get headers relevant to the host
    if "range" in request_headers.keys():
        headers.update({"range": request_headers["range"]})

    if "accept" in request_headers.keys():
        headers.update({"accept": request_headers["accept"]})

    # start session and request outside of a context managers
    session = aiohttp.ClientSession()
    response = await session.get(url, headers=headers)

    # get response header as a dict
    response_headers = {key.lower(): response.headers.get(key) for key in response.headers.keys()}

    # remove host's CORS restrictions from response headers
    if "access-control-allow-origin" in response_headers.keys():
        response_headers.update({"access-control-allow-origin": "*"})

    # modify hls streams to use local proxy
    if response_headers["content-type"] in HLS_CONTENT_TYPE_HEADERS:
        updated_content = add_proxy_to_hls_parts(await response.text())
        return Response(
            updated_content,
            response.status,
            headers=response_headers,
        )

    else:
        # return stream
        return StreamingResponse(
            yield_chunks(request, session, response),
            headers=response_headers,
            status_code=response.status,
        )


# TODO: block big files from being cached
async def cache_proxy(url: str, headers: dict, expires: str | None, db: AsyncSession):
    # check if the url host is on the allow list
    check_allowed_urls(url)

    # read or create the cache metadata record
    cache_meta_service = CacheMetaService(db)
    cache_meta = await cache_meta_service.create_or_read_from_url(url, headers, expires)

    # get the path to the cached file
    cache_path = os.path.join(CACHE_DIR, cache_meta.id)

    # get response headers and make all the keys lowercase
    response_headers = ast.literal_eval(cache_meta.response_headers)
    response_headers = {key.lower(): response_headers[key] for key in response_headers.keys()}

    # remove "content-encoding" header and also "content-length" if the former is removed succesfully
    # this is done to avoid mismatch between the original encoding/size and the one from the cached file
    try:
        response_headers.pop("content-encoding")
        response_headers.pop("content-length")
    except KeyError:
        pass

    # send de cached request and file to the user
    # this will return the original response even if it has an error status code
    return FileResponse(
        cache_path,
        status_code=cache_meta.response_status,
        headers=response_headers,
    )
