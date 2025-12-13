from typing import Any

from pydantic import BaseModel, ConfigDict


class MovieSourceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    url: str
    headers: dict[str, Any] = {}


class SeriesSourceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    season: int
    episode: int
    url: str
    headers: dict[str, Any] = {}


class MovieSourceCreate(MovieSourceBase):
    pass


class SeriesSourceCreate(SeriesSourceBase):
    pass


class MovieSourceRead(BaseModel):
    code: str
    headers: dict[str, Any] = {}


class SeriesSourceRead(BaseModel):
    code: str
    season: int
    episode: int
    headers: dict[str, Any] = {}
