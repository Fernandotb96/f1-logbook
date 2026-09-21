from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db
from ..season_history import recalculate_season_history

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/", response_model=schemas.DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(
        driver: schemas.DriverCreate,
        db: Session = Depends(get_db),
        _current_admin: models.User = Depends(require_admin),
):
    """Create a new driver."""
    new_driver = models.Driver(**driver.model_dump())
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return new_driver


@router.get("/", response_model=list[schemas.DriverOut])
def list_drivers(db: Session = Depends(get_db)):
    """List all drivers."""
    return db.scalars(select(models.Driver)).all()


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get a single driver by ID."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )
    return driver


@router.patch("/{driver_id}", response_model=schemas.DriverOut)
def update_driver(
        driver_id: int,
        updated: schemas.DriverUpdate,
        db: Session = Depends(get_db),
        _current_admin: models.User = Depends(require_admin),
):
    """Partially update a driver. Only fields included in the request body are changed."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    for field, value in updated.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
        driver_id: int,
        db: Session = Depends(get_db),
        _current_admin: models.User = Depends(require_admin),
):
    """Delete a driver by ID."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    affected_seasons = db.scalars(
        select(models.Race.season)
        .join(models.RaceResult)
        .where(models.RaceResult.driver_id == driver_id)
        .distinct()
    ).all()
    db.delete(driver)
    db.flush()
    for season in affected_seasons:
        recalculate_season_history(season, db)
    db.commit()
