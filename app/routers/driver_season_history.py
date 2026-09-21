from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["driver season history"])


@router.get(
    "/drivers/{driver_id}/season-history",
    response_model=list[schemas.DriverSeasonHistoryOut],
)
def list_driver_season_history(driver_id: int, db: Session = Depends(get_db)):
    """List a driver's calculated history by season."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    statement = (
        select(models.DriverSeasonHistory)
        .where(models.DriverSeasonHistory.driver_id == driver_id)
        .order_by(models.DriverSeasonHistory.season.desc())
    )
    return db.scalars(statement).all()


@router.get("/drivers/{driver_id}/stats", response_model=schemas.DriverStatsOut)
def get_driver_stats(driver_id: int, db: Session = Depends(get_db)):
    """Return a driver's calculated totals across all recorded seasons."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    histories = db.scalars(
        select(models.DriverSeasonHistory).where(
            models.DriverSeasonHistory.driver_id == driver_id
        )
    ).all()
    return schemas.DriverStatsOut(
        driver_id=driver_id,
        races_entered=sum(history.races_entered for history in histories),
        wins=sum(history.wins for history in histories),
        podiums=sum(history.podiums for history in histories),
        points=sum(history.points for history in histories),
        championships_won=sum(
            history.is_champion for history in histories
        ),
    )


@router.get(
    "/seasons/{season}/standings",
    response_model=list[schemas.DriverSeasonHistoryOut],
)
def list_season_standings(season: int, db: Session = Depends(get_db)):
    """List the calculated championship standings for one recorded season."""
    statement = (
        select(models.DriverSeasonHistory)
        .where(models.DriverSeasonHistory.season == season)
        .order_by(models.DriverSeasonHistory.championship_position)
    )
    return db.scalars(statement).all()
