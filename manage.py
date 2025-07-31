import argparse
import asyncio

import uvicorn


def runserver(protocol: str, address: str, disable_cache: bool):
    from urllib.parse import urljoin

    from src.app.main import app
    from src.app import config

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
            )

        case "https":
            uvicorn.run(
                app,
                host=host,
                port=int(port),
                ssl_certfile="localhost.crt",
                ssl_keyfile="localhost.key",
            )


async def clearcache():
    from sqlalchemy import select

    from src.app.proxy.services import CacheMetaService
    from src.app.proxy.models import CacheMeta
    from src.app.db import SessionLocal

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
        "protocol",
        choices=["http", "https"],
        default="http",
        help="The protocol used used by the server.",
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
            runserver(args.protocol, args.address, args.disable_cache)

        case "clearcache":
            asyncio.run(clearcache())


if __name__ == "__main__":
    main()
