from __future__ import annotations
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.errors import PydanticSchemaGenerationError

from ..types import LangChoices, MediaChoices
from ..models import Movie


class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str

    year: int
    media_type: MediaChoices = MediaChoices("movie")
    rating: Optional[float]
    translations: Optional[list["TranslatableMovieInfoBase"]] = []

    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None


class MovieBaseTranslated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str

    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None

    year: int
    media_type: MediaChoices = MediaChoices("movie")
    rating: Optional[float]

    logo: Optional[str] = None
    background: Optional[str] = None

    @classmethod
    def from_movie_model(cls, movie: Movie, lang: LangChoices) -> MovieBaseTranslated:
        translation = None
        for model in movie.translations:
            if model.lang.value == lang.value:
                translation = model
                break

        if translation is None:
            msg = "The specified movie does not contain the target translation"
            raise PydanticSchemaGenerationError(msg)

        return MovieBaseTranslated(
            imdb_code=movie.imdb_code,
            lang=translation.lang,
            name=translation.name,
            synopsis=translation.synopsis,
            poster=translation.poster,
            year=movie.year,
            rating=movie.rating,
            logo=movie.logo,
            background=movie.background,
        )


class MovieCreate(BaseModel):
    imdb_code: str

    year: int
    rating: Optional[float]

    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None


class TranslatableMovieInfoCreate(BaseModel):
    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None


class TranslatableMovieInfoBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lang: LangChoices
    name: str
    synopsis: str
    poster: Optional[str] = None
