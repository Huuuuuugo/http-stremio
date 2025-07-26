from __future__ import annotations
from urllib.parse import urlencode
import asyncio
import typing
import re

from bs4 import BeautifulSoup
import aiohttp

from .exceptions import *


class IMDB:
    def __init__(self, id: str, title: str, year: int, html: BeautifulSoup | None = None, cache_url: str | None = None):
        self.id = id
        self.title = title
        self.year = year
        self._html = html
        self._cache_url = cache_url

    def __str__(self):
        return f"<title: {self.title} | year: {self.year}>"

    async def related_media(self) -> list[IMDB]:
        related_media = self._html.find("section", {"data-testid": "MoreLikeThis"})
        related_media = related_media.find("div", {"data-testid": "shoveler"})
        related_media = related_media.find("div", {"data-testid": "shoveler-items-container"})

        tasks = []
        for item in related_media.find_all("div", {"class": "ipc-poster-card"}):
            media_href = item.find("div", {"class": "ipc-poster"}).find("a").get("href")
            media_id = re.findall(r"(tt\d+)", media_href)[0]
            tasks.append(IMDB.get(media_id, "pt", self._cache_url))

        return await asyncio.gather(*tasks)

    @classmethod
    async def search(cls, term: str, cache_url: str | None = None) -> list[IMDB]:
        url = f"https://v3.sg.media-imdb.com/suggestion/x/{term}.json?includeVideos=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                results = await res.json()
                results = results["d"]

        async def imdb_ignore_errors(code: str):
            try:
                return await IMDB.get(code, "pt", cache_url)
            except:
                pass

        tasks = []
        for result in results:
            id = result["id"]
            if re.match(r"tt\d+", id):
                tasks.append(imdb_ignore_errors(id))

        results_list = await asyncio.gather(*tasks)
        results_list = [result for result in results_list if result is not None]
        return results_list

    @classmethod
    async def get(cls, code: str, lang: typing.Literal["en", "fr", "de", "es", "pt", "ja", "zh"] = "en", cache_url: None | str = None) -> IMDB:
        # list of languages accepted by imdb
        accept_languages = {
            "en": "en-US,en;q=0.9",  # US English
            "fr": "fr-FR,fr;q=0.9",  # French
            "de": "de-DE,de;q=0.9",  # German
            "es": "es-ES,es;q=0.9",  # Spanish (Spain)
            "pt": "pt-BR,pt;q=0.9",  # Brazilian Portuguese
            "ja": "ja-JP,ja;q=0.9",  # Japanese
            "zh": "zh-CN,zh;q=0.9",  # Simplified Chinese
        }

        # get header value for the specified language
        try:
            lang = accept_languages[lang]
        except KeyError:
            msg = f"Invalid value for attribute 'lang'. Got '{lang}', expected any of the following: ['en', 'fr', 'de', 'es', 'pt', 'ja', 'zh']"
            raise AttributeError(msg)

        # get media page
        async with aiohttp.ClientSession() as session:
            imdb_url = f"https://www.imdb.com/title/{code}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
                "Accept-Language": lang,
            }

            if cache_url:
                query = urlencode({"url": imdb_url, "headers": headers})
                imdb_url = f"{cache_url}?{query}"
                headers = {}

            async with session.get(imdb_url, headers=headers) as response:
                if response.status != 200:
                    msg = f"Bad status code when requesting IMDb page. Expected '200', got '{response.status}'"
                    raise Exception(msg)

                imdb_html = BeautifulSoup(await response.text(), "html.parser")

        # get title
        title = imdb_html.find("h1").text
        if not title:
            msg = "Error while parsing IMDb page. Could not find 'title'."
            raise IMDBParsingError(msg)

        # get release year by finding an 'li' element with exactly 4 integers
        year = 0
        for ul in imdb_html.find_all("ul"):
            ul: BeautifulSoup
            li_elements = ul.find_all("li", {"class": "ipc-inline-list__item"})
            for li in li_elements:
                text = li.text.strip()
                matches = re.match(r"\d{4}", text)
                if matches:
                    year = int(matches[0])
        if not year:
            msg = "Error while parsing IMDb page. Could not find 'year'"
            raise IMDBParsingError(msg)

        return IMDB(code, title, year, imdb_html)


async def main():
    tasks = [
        IMDB.get("tt1305826"),
        IMDB.get("tt32149847"),
        IMDB.get("tt23649128"),
        IMDB.get("tt31806037"),
        IMDB.get("tt11280740"),
    ]

    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
