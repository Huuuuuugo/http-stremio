import argparse
import asyncio

import uvicorn


def runserver(protocol: str, address: str):
    from src.app.main import app

    host, port = address.split(":")

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
        help="The ip address and port where the server will run in the form of a string formatted as 'host:port'.",
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
            runserver(args.protocol, args.address)

        case "clearcache":
            asyncio.run(clearcache())


if __name__ == "__main__":
    main()
