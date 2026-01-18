import argparse
import asyncio
import os
import uvicorn
from dotenv import load_dotenv
load_dotenv()


def runserver(protocol: str, address: str, disable_cache: bool):
    from urllib.parse import urljoin

    from src.app import config
    from src.app.main import app
    from src.utils.logger_config import LogConfig

    host, port = address.split(":")
    server_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    config.LOCAL_ADDRESS = f"{protocol}://{server_host}:{port}/"
    if not disable_cache:
        config.CACHE_URL = urljoin(config.LOCAL_ADDRESS, "/proxy/cache/")

    match protocol:
        case "http":
            uvicorn.run(
                app,
                host=host,
                port=int(port),
                log_config=LogConfig().model_dump(),
            )

        case "https":
            uvicorn.run(
                app,
                host=host,
                port=int(port),
                ssl_certfile="certs/localhost.crt",
                ssl_keyfile="certs/localhost.key",
                log_config=LogConfig().model_dump(),
            )


async def clearcache():
    from sqlalchemy import select

    from src.app.db import SessionLocal
    from src.app.proxy.models import CacheMeta
    from src.app.proxy.services import CacheMetaService

    async with SessionLocal() as db:
        stmt = select(CacheMeta)
        results = await db.execute(stmt)
        results = [instance.id for instance in results.scalars().all()]

        cache_meta_service = CacheMetaService(db)

        tasks = []
        for id in results:
            tasks.append(cache_meta_service.delete(id))

        await asyncio.gather(*tasks)


def main():
    # argparser setup
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command",
        help="Avaliable commands:",
        required=True,
    )

    # arguments for running the server
    runserver_parser = subparsers.add_parser(
        "runserver",
        help="Starts the http/https server.",
    )
    runserver_parser.add_argument(
    "--protocol",
    choices=["http", "https"],
    help="Protocol used by the server (overrides APP_PROTOCOL).",
    )
    runserver_parser.add_argument(
        "--address",
        "-a",
        type=str,
        default="0.0.0.0:6222",
        help="A string formatted as 'host:port' containing the IP address and port where the server should run.",
    )
    runserver_parser.add_argument(
        "--disable-cache",
        "-dc",
        action="store_true",
        help="If present, the cache proxy will not be used internally.",
    )

    # arguments for clearing cached files
    clearcache_parser = subparsers.add_parser(
        "clearcache",
        help="Clears all cached files from the disk and database.",
    )

    # parse args and run command
    args = parser.parse_args()
    match args.command:
        case "runserver":
            protocol = (
                args.protocol
                or os.getenv("APP_PROTOCOL", "http")
            )

            address = (
                args.address
                or os.getenv("APP_ADDRESS", "0.0.0.0:6222")
            )

            disable_cache = (
                args.disable_cache
                or os.getenv("DISABLE_CACHE", "false").lower() == "true"
            )
            runserver(protocol, address, disable_cache)

        case "clearcache":
            asyncio.run(clearcache())


if __name__ == "__main__":
    main()
