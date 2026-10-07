from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Authentication
# =============================================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserAdminUpdate(BaseModel):
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =============================================================================
# Reference data: drivers, circuits, constructors
# =============================================================================

class DriverBase(BaseModel):
    jolpica_id: Optional[str] = None
    name: str
    nationality: Optional[str] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    jolpica_id: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class DriverOut(DriverBase):
    id: int

    class Config:
        from_attributes = True


class CircuitBase(BaseModel):
    jolpica_id: Optional[str] = None
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    length_km: Optional[float] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class CircuitCreate(CircuitBase):
    pass


class CircuitUpdate(BaseModel):
    jolpica_id: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    length_km: Optional[float] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class CircuitOut(CircuitBase):
    id: int

    class Config:
        from_attributes = True


class ConstructorBase(BaseModel):
    jolpica_id: Optional[str] = None
    name: str
    nationality: Optional[str] = None


class ConstructorCreate(ConstructorBase):
    pass


class ConstructorUpdate(BaseModel):
    jolpica_id: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None


class ConstructorOut(ConstructorBase):
    id: int

    class Config:
        from_attributes = True


# =============================================================================
# Seasons
# =============================================================================

class SeasonBase(BaseModel):
    year: int
    is_completed: bool = False


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    is_completed: Optional[bool] = None


class SeasonOut(SeasonBase):
    class Config:
        from_attributes = True


# =============================================================================
# Races
# =============================================================================

class RaceBase(BaseModel):
    name: str
    season: int
    round: int
    race_date: date
    circuit_id: int


class RaceCreate(RaceBase):
    pass


class RaceUpdate(BaseModel):
    name: Optional[str] = None
    season: Optional[int] = None
    round: Optional[int] = None
    race_date: Optional[date] = None
    circuit_id: Optional[int] = None


class RaceOut(RaceBase):
    id: int
    circuit: CircuitOut

    class Config:
        from_attributes = True


# =============================================================================
# Results: race classification and sprint sessions
# =============================================================================

class RaceResultCreate(BaseModel):
    driver_id: int
    constructor_id: Optional[int] = None
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: float = 0.0
    status: Optional[str] = None
    fastest_lap_time_ms: Optional[int] = None


class RaceResultUpdate(BaseModel):
    constructor_id: Optional[int] = None
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: Optional[float] = None
    status: Optional[str] = None
    fastest_lap_time_ms: Optional[int] = None


class RaceResultOut(BaseModel):
    id: int
    race_id: int
    driver_id: int
    constructor_id: Optional[int]
    grid_position: Optional[int]
    position: Optional[int]
    points: float
    status: Optional[str]
    fastest_lap_time_ms: Optional[int]
    driver: DriverOut
    constructor: Optional[ConstructorOut]

    class Config:
        from_attributes = True


class SprintResultCreate(BaseModel):
    driver_id: int
    constructor_id: Optional[int] = None
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: float = 0.0
    status: Optional[str] = None


class SprintResultUpdate(BaseModel):
    constructor_id: Optional[int] = None
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: Optional[float] = None
    status: Optional[str] = None


class SprintResultOut(BaseModel):
    id: int
    race_id: int
    driver_id: int
    constructor_id: Optional[int]
    grid_position: Optional[int]
    position: Optional[int]
    points: float
    status: Optional[str]
    driver: DriverOut
    constructor: Optional[ConstructorOut]

    class Config:
        from_attributes = True


# =============================================================================
# User favourites
# =============================================================================

class FavoriteDriverCreate(BaseModel):
    driver_id: int


class FavoriteDriverOut(BaseModel):
    id: int
    user_id: int
    driver_id: int
    driver: DriverOut

    class Config:
        from_attributes = True


class FavoriteCircuitCreate(BaseModel):
    circuit_id: int


class FavoriteCircuitOut(BaseModel):
    id: int
    user_id: int
    circuit_id: int
    circuit: CircuitOut

    class Config:
        from_attributes = True


class FavoriteRaceCreate(BaseModel):
    race_id: int


class FavoriteRaceOut(BaseModel):
    id: int
    user_id: int
    race_id: int
    race: RaceOut

    class Config:
        from_attributes = True


# =============================================================================
# Derived data: statistics and standings
# =============================================================================

class DriverSeasonHistoryOut(BaseModel):
    id: int
    driver_id: int
    season: int
    races_entered: int
    wins: int
    podiums: int
    sprints_entered: int
    sprint_wins: int
    sprint_podiums: int
    points: float
    championship_position: int
    is_champion: bool
    driver: DriverOut

    class Config:
        from_attributes = True


class DriverStatsOut(BaseModel):
    driver_id: int
    races_entered: int
    wins: int
    podiums: int
    sprints_entered: int
    sprint_wins: int
    sprint_podiums: int
    points: float
    championships_won: int


class CircuitLapRecordOut(BaseModel):
    circuit_id: int
    race_id: int
    race_name: str
    driver_id: int
    fastest_lap_time_ms: int
    driver: DriverOut


# =============================================================================
# Synchronisation
# =============================================================================

class SyncEntityCountOut(BaseModel):
    created: int
    updated: int


class SeasonSyncOut(BaseModel):
    season: int
    is_completed: bool
    seasons: SyncEntityCountOut
    circuits: SyncEntityCountOut
    drivers: SyncEntityCountOut
    constructors: SyncEntityCountOut
    races: SyncEntityCountOut
    race_results: SyncEntityCountOut
    sprint_results: SyncEntityCountOut
