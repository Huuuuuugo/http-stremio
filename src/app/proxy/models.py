from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import types


class Base(DeclarativeBase):
    pass


class CacheMeta(Base):
    __tablename__ = "cachemeta"

    id: Mapped[str] = mapped_column(types.String(length=32), nullable=False, unique=True, primary_key=True)
    is_downloaded: Mapped[bool] = mapped_column(types.Boolean, nullable=True)
    cache_size: Mapped[int] = mapped_column(types.Integer, nullable=True)

    # request_method: Mapped[str]
    request_url: Mapped[str] = mapped_column(types.String, nullable=False)
    request_headers: Mapped[str] = mapped_column(types.String, nullable=False)
    # request_body: Mapped[str]

    response_headers: Mapped[str] = mapped_column(types.String, nullable=True)
    response_status: Mapped[int] = mapped_column(types.Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(types.DateTime, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(types.DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(types.DateTime, nullable=True)
    relative_expires_str: Mapped[str] = mapped_column(types.String, nullable=True)

    def __repr__(self):
        return f"<CacheMeta(id={self.id}, request_url={self.request_url}, created_at={self.created_at})>"

    def to_json(self):
        return {
            "id": self.id,
            "is_downloaded": self.is_downloaded,
            "cache_size": self.cache_size,
            "request_url": self.request_url,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "response_status": self.response_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "relative_expires_str": self.relative_expires_str,
        }
