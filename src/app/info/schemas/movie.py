from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..models import LangChoices, MediaChoices


class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    imdb_code: str
    lang: LangChoices

    name: str
    year: int
    media_type: MediaChoices
    synopsis: str
    rating: Optional[float]

    poster: Optional[str] = None
    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None


class MovieCreate(BaseModel):
    imdb_code: str
    lang: LangChoices

    name: str
    year: int
    media_type: MediaChoices
    synopsis: str
    rating: Optional[float]

    poster: Optional[str] = None
    logo: Optional[str] = None
    background: Optional[str] = None

    update_at: Optional[datetime] = None
