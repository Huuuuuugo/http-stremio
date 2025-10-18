from pydantic import BaseModel, ConfigDict
from typing import Optional


class EpisodeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season: int
    episode: int
    name: str
    synopsis: str
    image: Optional[str] = None


class EpisodeCreate(BaseModel):
    season: int
    episode: int
    name: str
    synopsis: str
    image: Optional[str] = None
