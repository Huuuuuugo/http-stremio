from __future__ import annotations
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.errors import PydanticSchemaGenerationError

from ..types import LangChoices, MediaChoices
from ..models import Series
from .episode import EpisodeBase


class SeriesBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str

    year: int
    end_year: Optional[int]
    media_type: MediaChoices = MediaChoices("series")
    rating: Optional[float]
    translations: Optional[list["TranslatableSeriesInfoBase"]] = []

    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None

    episodes: list[EpisodeBase]


class SeriesBaseTranslated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str

    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None

    year: int
    end_year: Optional[int]
    media_type: MediaChoices = MediaChoices("series")
    rating: Optional[float]

    logo: Optional[str] = None
    background: Optional[str] = None

    episodes: list[EpisodeBase]

    @classmethod
    def from_series_model(cls, series: Series, lang: LangChoices) -> SeriesBaseTranslated:
        translation = None
        for model in series.translations:
            if model.lang.value == lang.value:
                translation = model
                break

        if translation is None:
            msg = "The specified movie does not contain the target translation"
            raise PydanticSchemaGenerationError(msg)

        episodes = []
        for episode in series.episodes:
            episodes.append(EpisodeBase.model_validate(episode))

        return SeriesBaseTranslated(
            imdb_code=series.imdb_code,
            lang=translation.lang,
            name=translation.name,
            synopsis=translation.synopsis,
            poster=translation.poster,
            year=series.year,
            end_year=series.end_year,
            rating=series.rating,
            logo=series.logo,
            background=series.background,
            episodes=episodes,
        )


class SeriesCreate(BaseModel):
    imdb_code: str

    year: int
    end_year: Optional[int]
    rating: Optional[float]

    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None


class TranslatableSeriesInfoCreate(BaseModel):
    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None


class TranslatableSeriesInfoBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None
