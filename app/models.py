from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column()
    team: Mapped[Optional[str]] = mapped_column()
    wins_total: Mapped[int] = mapped_column(default=0)
    championships_won: Mapped[int] = mapped_column(default=0)
    photo_url: Mapped[Optional[str]] = mapped_column()
    photo_credit: Mapped[Optional[str]] = mapped_column()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class FavoriteDriver(Base):
    __tablename__ = "favorite_drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    driver: Mapped[Driver] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("user_id", "driver_id"),)
