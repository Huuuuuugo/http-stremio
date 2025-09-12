from enum import Enum
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint

from src.app.db import Base


class MediaChoices(Enum):
    movie = "movie"
    series = "series"


class LangChoices(Enum):
    en = "en"
    fr = "fr"
    de = "de"
    es = "es"
    pt = "pt"
    ja = "ja"
    zh = "zh"


class Movie(Base):
    __tablename__ = "movie"
    __table_args__ = (UniqueConstraint("imdb_code", "lang", name="unq_imdb_lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    imdb_code: Mapped[str] = mapped_column()
    lang: Mapped[LangChoices] = mapped_column()

    name: Mapped[str] = mapped_column()
    year: Mapped[int] = mapped_column()
    media_type: Mapped[MediaChoices] = mapped_column()
    synopsis: Mapped[str] = mapped_column()
    rating: Mapped[float] = mapped_column()

    poster: Mapped[str] = mapped_column(nullable=True)
    logo: Mapped[str] = mapped_column(nullable=True)
    background: Mapped[str] = mapped_column(nullable=True)

    update_at: Mapped[datetime] = mapped_column(nullable=True)


class Series(Base):
    __tablename__ = "series"
    __table_args__ = (UniqueConstraint("imdb_code", "lang", name="unq_imdb_lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    imdb_code: Mapped[str] = mapped_column()
    lang: Mapped[LangChoices] = mapped_column()

    name: Mapped[str] = mapped_column()
    start_year: Mapped[int] = mapped_column()
    end_year: Mapped[int] = mapped_column()
    media_type: Mapped[MediaChoices] = mapped_column()
    synopsis: Mapped[str] = mapped_column()
    rating: Mapped[float] = mapped_column()

    episodes: Mapped[list["Episode"]] = relationship(back_populates="series", lazy="selectin")

    poster: Mapped[str] = mapped_column(nullable=True)
    logo: Mapped[str] = mapped_column(nullable=True)
    background: Mapped[str] = mapped_column(nullable=True)

    update_at: Mapped[datetime] = mapped_column(nullable=True)


class Episode(Base):
    __tablename__ = "episode"

    id: Mapped[int] = mapped_column(primary_key=True)

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"))
    series: Mapped["Series"] = relationship(back_populates="episodes", lazy="joined")

    season: Mapped[int] = mapped_column()
    episode: Mapped[int] = mapped_column()

    name: Mapped[str] = mapped_column()
    synopsis: Mapped[str] = mapped_column()
    image: Mapped[str] = mapped_column(nullable=True)
