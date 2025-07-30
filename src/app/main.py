from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import html_pages, proxy, stremio, info
from .db import init_db
from .test_routes import router as tests_router


async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan, debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(html_pages.router)
app.include_router(proxy.router)
app.include_router(stremio.router)
app.include_router(info.router)
app.include_router(tests_router)
