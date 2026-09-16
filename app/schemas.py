from datetime import datetime
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
