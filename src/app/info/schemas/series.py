from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..models import LangChoices, MediaChoices
from .episode import EpisodeBase


class SeriesBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str
    lang: LangChoices

    name: str
    year: int
    end_year: Optional[int]
    media_type: MediaChoices
    synopsis: str
    rating: Optional[float]

    poster: Optional[str] = None
    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None

    episodes: list[EpisodeBase]


class SeriesCreate(BaseModel):
    imdb_code: str
    lang: LangChoices

    name: str
    year: int
    end_year: Optional[int]
    media_type: MediaChoices
    synopsis: str
    rating: Optional[float]

    poster: Optional[str] = None
    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None
