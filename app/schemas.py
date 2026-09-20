from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class DriverBase(BaseModel):
    name: str
    nationality: Optional[str] = None
    team: Optional[str] = None
    wins_total: Optional[int] = 0
    championships_won: Optional[int] = 0
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    team: Optional[str] = None
    wins_total: Optional[int] = None
    championships_won: Optional[int] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class DriverOut(DriverBase):
    id: int

    class Config:
        from_attributes = True


class CircuitBase(BaseModel):
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    length_km: Optional[float] = None
    lap_record: Optional[str] = None
    lap_record_driver: Optional[str] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class CircuitCreate(CircuitBase):
    pass


class CircuitUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    length_km: Optional[float] = None
    lap_record: Optional[str] = None
    lap_record_driver: Optional[str] = None
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None


class CircuitOut(CircuitBase):
    id: int

    class Config:
        from_attributes = True


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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class FavoriteRaceCreate(BaseModel):
    race_id: int


class FavoriteRaceOut(BaseModel):
    id: int
    user_id: int
    race_id: int
    race: RaceOut

    class Config:
        from_attributes = True


class RaceResultCreate(BaseModel):
    driver_id: int
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: float = 0.0
    status: Optional[str] = None


class RaceResultUpdate(BaseModel):
    grid_position: Optional[int] = None
    position: Optional[int] = None
    points: Optional[float] = None
    status: Optional[str] = None


class RaceResultOut(BaseModel):
    id: int
    race_id: int
    driver_id: int
    grid_position: Optional[int]
    position: Optional[int]
    points: float
    status: Optional[str]
    driver: DriverOut

    class Config:
        from_attributes = True
