from typing import Any

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from .db import Base


class MovieSource(Base):
    __tablename__ = "movie_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=True)
    url: Mapped[str] = mapped_column(nullable=False, unique=True)
    headers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})


class SeriesSource(Base):
    __tablename__ = "series_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=True)
    episode: Mapped[int] = mapped_column(nullable=False)
    season: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False, unique=True)
    headers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
