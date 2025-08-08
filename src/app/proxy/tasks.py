import asyncio

from sqlalchemy import select

from ..db import SessionLocal
from .models import CacheMeta
from .services import CacheMetaService
from .utils import get_dir_size
from .constants import CACHE_DIR, MAX_CACHE_DIR_SIZE

batch_delete_lock = asyncio.Lock()


async def delete_exceeding_caches():
    # check if the size limit has been reached
    if get_dir_size(CACHE_DIR) >= MAX_CACHE_DIR_SIZE:
        async with SessionLocal() as db:
            cache_meta_service = CacheMetaService(db)
            async with batch_delete_lock:
                # query all cache metas ordered by the last time they were used
                stmt = select(CacheMeta).order_by(CacheMeta.last_used_at)
                results = await db.execute(stmt)

                # mark cache metas to be deleted until the number of exceeding bytes goes bellow zero
                exceeding_bytes = get_dir_size(CACHE_DIR) - MAX_CACHE_DIR_SIZE
                tasks = []
                for cache_meta in results.scalars().all():
                    if exceeding_bytes < 0:
                        break

                    # mark the cache to be deleted and subtract its size from the exceeding bytes
                    tasks.append(cache_meta_service.delete(cache_meta.id))
                    try:
                        exceeding_bytes -= cache_meta.cache_size
                    except TypeError:
                        pass

                # delete all the marked downloads simultaneously
                await asyncio.gather(*tasks)


async def repeat_tasks(delay: float):
    while True:
        await delete_exceeding_caches()
        await asyncio.sleep(delay)
