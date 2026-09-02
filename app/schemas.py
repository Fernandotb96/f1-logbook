from typing import Optional
from pydantic import BaseModel


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


class DriverUpdate(DriverBase):
    pass


class DriverOut(DriverBase):
    id: int

    class Config:
        from_attributes = True
