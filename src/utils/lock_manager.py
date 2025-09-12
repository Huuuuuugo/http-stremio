import asyncio


class DynamicLockManager:
    def __init__(self, max_locks: int = 255):
        self._max_locks = max_locks
        self._locks = {}
        self._manager_lock = asyncio.Lock()

    async def get_lock(self, key: str):
        async with self._manager_lock:
            # create new lock if doesn't exist already
            if key not in self._locks.keys():
                # clear locks after a certain threshold
                if len(self._locks) >= self._max_locks:
                    for key in self._locks.keys():
                        if not self._locks[key].locked():
                            del self._locks[key]
                            break

                # create and save lock
                lock = asyncio.Lock()
                self._locks[key] = lock
            else:
                lock = self._locks[key]

        return lock
