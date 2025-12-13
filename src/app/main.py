from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import website, proxy, stremio, info
from .db import init_db
from .proxy.tasks import repeat_tasks


# TODO: think of a more scalable way to run repeated tasks from any app
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(repeat_tasks(30))
    yield


app = FastAPI(lifespan=lifespan, debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(website.router)
app.include_router(proxy.router)
app.include_router(stremio.router)
app.include_router(info.router)
