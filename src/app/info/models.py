from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint

from src.app.db import Base
from .types import LangChoices, MediaChoices


class TranslatableMovieInfo(Base):
    __tablename__ = "translatable_movie_info"
    __table_args__ = (UniqueConstraint("movie_id", "lang", name="unq_media_lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"))
    movie: Mapped["Movie"] = relationship(back_populates="translations", lazy="joined")

    lang: Mapped[LangChoices] = mapped_column()
    name: Mapped[str] = mapped_column()
    synopsis: Mapped[str] = mapped_column()
    poster: Mapped[str] = mapped_column(nullable=True)


class Movie(Base):
    __tablename__ = "movie"
    __table_args__ = (UniqueConstraint("imdb_code", name="unq_imdb"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    imdb_code: Mapped[str] = mapped_column()

    year: Mapped[int] = mapped_column()
    media_type: Mapped[MediaChoices] = mapped_column()
    rating: Mapped[float] = mapped_column(nullable=True)
    translations: Mapped[list[TranslatableMovieInfo]] = relationship(back_populates="movie", lazy="selectin")

    logo: Mapped[str] = mapped_column(nullable=True)
    background: Mapped[str] = mapped_column(nullable=True)

    update_at: Mapped[datetime] = mapped_column(nullable=True)


class TranslatableSeriesInfo(Base):
    __tablename__ = "translatable_series_info"
    __table_args__ = (UniqueConstraint("series_id", "lang", name="unq_media_lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"))
    series: Mapped["Series"] = relationship(back_populates="translations", lazy="joined")

    lang: Mapped[LangChoices] = mapped_column()
    name: Mapped[str] = mapped_column()
    synopsis: Mapped[str] = mapped_column()
    poster: Mapped[str] = mapped_column(nullable=True)


class Series(Base):
    __tablename__ = "series"
    __table_args__ = (UniqueConstraint("imdb_code", name="unq_imdb"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    imdb_code: Mapped[str] = mapped_column()

    year: Mapped[int] = mapped_column()
    end_year: Mapped[int] = mapped_column(nullable=True)
    media_type: Mapped[MediaChoices] = mapped_column()
    rating: Mapped[float] = mapped_column(nullable=True)
    translations: Mapped[list[TranslatableSeriesInfo]] = relationship(back_populates="series", lazy="selectin")

    episodes: Mapped[list["Episode"]] = relationship(back_populates="series", lazy="selectin")

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
