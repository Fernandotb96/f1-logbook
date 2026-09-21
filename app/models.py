from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jolpica_id: Mapped[Optional[str]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column()
    photo_url: Mapped[Optional[str]] = mapped_column()
    photo_credit: Mapped[Optional[str]] = mapped_column()


class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jolpica_id: Mapped[Optional[str]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    location: Mapped[Optional[str]] = mapped_column()
    country: Mapped[Optional[str]] = mapped_column()
    length_km: Mapped[Optional[float]] = mapped_column()
    photo_url: Mapped[Optional[str]] = mapped_column()
    photo_credit: Mapped[Optional[str]] = mapped_column()


class Constructor(Base):
    __tablename__ = "constructors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jolpica_id: Mapped[Optional[str]] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column()


class Season(Base):
    __tablename__ = "seasons"

    year: Mapped[int] = mapped_column(primary_key=True)
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )


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
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )


class FavoriteDriver(Base):
    __tablename__ = "favorite_drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    driver: Mapped[Driver] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("user_id", "driver_id"),)


class FavoriteCircuit(Base):
    __tablename__ = "favorite_circuits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("circuits.id", ondelete="CASCADE"),
        nullable=False,
    )
    circuit: Mapped[Circuit] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("user_id", "circuit_id"),)


class Race(Base):
    __tablename__ = "races"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    season: Mapped[int] = mapped_column(
        ForeignKey("seasons.year"),
        nullable=False,
    )
    round: Mapped[int] = mapped_column(nullable=False)
    race_date: Mapped[date] = mapped_column(nullable=False)
    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("circuits.id", ondelete="CASCADE"),
        nullable=False,
    )
    circuit: Mapped[Circuit] = relationship(lazy="joined")
    results: Mapped[list["RaceResult"]] = relationship(
        back_populates="race",
        cascade="all, delete-orphan",
    )
    __table_args__ = (UniqueConstraint("season", "round"),)


class FavoriteRace(Base):
    __tablename__ = "favorite_races"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"),
        nullable=False,
    )
    race: Mapped[Race] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("user_id", "race_id"),)


class RaceResult(Base):
    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"),
        nullable=False,
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    constructor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("constructors.id", ondelete="SET NULL"),
    )
    grid_position: Mapped[Optional[int]] = mapped_column()
    position: Mapped[Optional[int]] = mapped_column()
    points: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[Optional[str]] = mapped_column()
    fastest_lap_time_ms: Mapped[Optional[int]] = mapped_column()
    race: Mapped[Race] = relationship(back_populates="results")
    driver: Mapped[Driver] = relationship(lazy="joined")
    constructor: Mapped[Optional[Constructor]] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("race_id", "driver_id"),)


class DriverSeasonHistory(Base):
    __tablename__ = "driver_season_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    season: Mapped[int] = mapped_column(
        ForeignKey("seasons.year"),
        nullable=False,
    )
    races_entered: Mapped[int] = mapped_column(default=0)
    wins: Mapped[int] = mapped_column(default=0)
    podiums: Mapped[int] = mapped_column(default=0)
    points: Mapped[float] = mapped_column(default=0.0)
    championship_position: Mapped[int] = mapped_column(nullable=False)
    is_champion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    driver: Mapped[Driver] = relationship(lazy="joined")
    __table_args__ = (UniqueConstraint("driver_id", "season"),)
