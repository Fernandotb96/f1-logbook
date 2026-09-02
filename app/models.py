from sqlalchemy import Column, Integer, String

from .database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nationality = Column(String, nullable=True)
    team = Column(String, nullable=True)
    wins_total = Column(Integer, default=0)
    championships_won = Column(Integer, default=0)
    photo_url = Column(String, nullable=True)
    photo_credit = Column(String, nullable=True)
