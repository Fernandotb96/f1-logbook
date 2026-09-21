from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db
from ..season_history import recalculate_season_history

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.post("/", response_model=schemas.SeasonOut, status_code=status.HTTP_201_CREATED)
def create_season(
    season: schemas.SeasonCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Create a season. Administrators only."""
    existing_season = db.scalar(
        select(models.Season).where(models.Season.year == season.year)
    )
    if existing_season:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Season already exists",
        )

    new_season = models.Season(**season.model_dump())
    db.add(new_season)
    db.commit()
    db.refresh(new_season)
    return new_season


@router.get("/", response_model=list[schemas.SeasonOut])
def list_seasons(db: Session = Depends(get_db)):
    """List all seasons from newest to oldest."""
    return db.scalars(select(models.Season).order_by(models.Season.year.desc())).all()


@router.get("/{year}", response_model=schemas.SeasonOut)
def get_season(year: int, db: Session = Depends(get_db)):
    """Get one season by year."""
    season = db.scalar(select(models.Season).where(models.Season.year == year))
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
    return season


@router.patch("/{year}", response_model=schemas.SeasonOut)
def update_season(
    year: int,
    updated: schemas.SeasonUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Update a season's completion state. Administrators only."""
    season = db.scalar(select(models.Season).where(models.Season.year == year))
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")

    for field, value in updated.model_dump(exclude_unset=True).items():
        setattr(season, field, value)

    db.flush()
    recalculate_season_history(year, db)
    db.commit()
    db.refresh(season)
    return season


@router.delete("/{year}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(
    year: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete an empty season. Administrators only."""
    season = db.scalar(select(models.Season).where(models.Season.year == year))
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")

    race = db.scalar(select(models.Race).where(models.Race.season == year))
    if race:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a season that has races",
        )

    db.delete(season)
    db.commit()
