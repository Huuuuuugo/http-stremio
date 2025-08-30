from __future__ import annotations
from urllib.parse import urlencode
import asyncio
import typing
import re

from bs4 import BeautifulSoup
import aiohttp


class IMDB:
    def __init__(self, id: str, lang: str, html: BeautifulSoup | None = None, cache_url: str | None = None):
        self.id = id
        self._lang = lang
        self._html = html
        self._cache_url = cache_url

    @property
    def title(self):
        # get title
        title = self._html.find("h1").text
        return title

    @property
    def year(self):
        # get release year by finding an 'li' element with exactly 4 integers
        year = None
        for ul in self._html.find_all("ul"):
            ul: BeautifulSoup
            li_elements = ul.find_all("li", {"class": "ipc-inline-list__item"})
            for li in li_elements:
                text = li.text.strip()
                matches = re.match(r"\d{4}", text)
                if matches:
                    year = int(matches[0])
                    break

        return year

    @property
    def end_year(self):
        end_year = None

        if self.type == "movie":
            end_year = self.year

        else:
            # get release year by finding an 'li' element with exactly 4 integers
            for ul in self._html.find_all("ul"):
                ul: BeautifulSoup
                li_elements = ul.find_all("li", {"class": "ipc-inline-list__item"})
                for li in li_elements:
                    text = li.text.strip()
                    matches = re.findall(r"^\d{4}.(\d{4})$", text)
                    if matches:
                        end_year = int(matches[0])
                        break

        return end_year

    @property
    def type(self):
        episodes_header = self._html.find("div", {"data-testid": "episodes-header"})
        if episodes_header:
            type = "series"
        else:
            type = "movie"

        return type

    @property
    def synopsis(self):
        synopsis = self._html.find("span", {"data-testid": "plot-xl"})
        if synopsis is not None:
            synopsis = synopsis.text

        return synopsis

    @property
    def rating(self):
        rating = self._html.find("span", {"class": "ipc-rating-star--rating"})
        if rating is not None:
            rating = rating.text
            rating = float(rating.replace(",", "."))

        return rating

    @property
    def poster(self):
        poster = self._html.find("div", {"data-testid": "hero-media__poster"}).find("img")
        if poster is not None:
            target_w = 480
            poster = poster.get("src")

            # get crop params from original image
            crop = re.findall(r"\._.*CR(\d+),(\d+),(\d+),(\d+)_.*\.jpg", poster)
            crop_str = ""
            if crop:
                # scale crop params to the new target width
                x, y, w, h = map(int, crop[0])
                scale = h / w

                target_h = round(target_w * scale)

                x = int(x * target_w / w)
                y = int(y * target_h / h)

                crop_str = f"CR{x},{y},{target_w},{target_h}"

            if "UY" in poster:
                dimension_str = f"UY{target_h}"
            else:
                dimension_str = f"UX{target_w}"

            poster = re.sub(r"\._.+_\.jpg", f"._V1_QL100_{dimension_str}_{crop_str}_.jpg", poster)

        return poster

    def __repr__(self):
        return f"<IMDB:(id={self.id}, title={self.title}, year={self.year})>"

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "type": self.type,
            "synopsis": self.synopsis,
            "rating": self.rating,
            "poster": self.poster,
        }

    async def get_related_media(self, ids_only: bool = False) -> list[IMDB]:
        related_media = self._html.find("section", {"data-testid": "MoreLikeThis"})
        related_media = related_media.find("div", {"data-testid": "shoveler"})
        related_media = related_media.find("div", {"data-testid": "shoveler-items-container"})

        media_ids = []
        for item in related_media.find_all("div", {"class": "ipc-poster-card"}):
            media_href = item.find("div", {"class": "ipc-poster"}).find("a").get("href")
            media_id = re.findall(r"(tt\d+)", media_href)[0]
            media_ids.append(media_id)

        if ids_only:
            return media_ids

        tasks = []
        for media_id in media_ids:
            tasks.append(get_media(media_id, self._lang, self._cache_url))

        return await asyncio.gather(*tasks)


async def get_media(
    id: str,
    lang: typing.Literal["en", "fr", "de", "es", "pt", "ja", "zh"] = "en",
    cache_url: None | str = None,
) -> IMDB:
    print(id)
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
        lang_header = accept_languages[lang]
    except KeyError:
        msg = f"Invalid value for attribute 'lang'. Got '{lang}', expected any of the following: ['en', 'fr', 'de', 'es', 'pt', 'ja', 'zh']"
        raise AttributeError(msg)

    # get media page
    async with aiohttp.ClientSession() as session:
        imdb_url = f"https://www.imdb.com/title/{id}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            "Accept-Language": lang_header,
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

    return IMDB(id, lang, html=imdb_html, cache_url=cache_url)


async def search(term: str, lang: str, cache_url: str | None = None) -> list[IMDB]:
    url = f"https://v3.sg.media-imdb.com/suggestion/x/{term}.json?includeVideos=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            results = await res.json()
            results = results["d"]

    tasks = []
    for result in results:
        id = result["id"]
        if re.match(r"tt\d+", id):
            tasks.append(get_media(id, lang, cache_url))

    results_list = await asyncio.gather(*tasks)
    results_list = [result for result in results_list if result is not None]
    return results_list


async def main():
    tasks = [
        get_media("tt1305826", cache_url="http://localhost:6132/proxy/cache/"),
        get_media("tt32149847", cache_url="http://localhost:6132/proxy/cache/"),
        get_media("tt23649128", cache_url="http://localhost:6132/proxy/cache/"),
        get_media("tt31806037", cache_url="http://localhost:6132/proxy/cache/"),
        get_media("tt11280740", cache_url="http://localhost:6132/proxy/cache/"),
    ]

    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
