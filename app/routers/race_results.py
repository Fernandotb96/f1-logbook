from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db
from ..season_history import recalculate_season_history

router = APIRouter(prefix="/races", tags=["race results"])


@router.get("/{race_id}/results", response_model=list[schemas.RaceResultOut])
def list_race_results(race_id: int, db: Session = Depends(get_db)):
    """List the recorded results for one race."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    statement = (
        select(models.RaceResult)
        .where(models.RaceResult.race_id == race_id)
        .order_by(models.RaceResult.position, models.RaceResult.id)
    )
    return db.scalars(statement).all()


@router.post(
    "/{race_id}/results",
    response_model=schemas.RaceResultOut,
    status_code=status.HTTP_201_CREATED,
)
def create_race_result(
    race_id: int,
    result: schemas.RaceResultCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Record one driver's result in a race. Administrators only."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    driver = db.scalar(select(models.Driver).where(models.Driver.id == result.driver_id))
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    if result.constructor_id is not None:
        constructor = db.scalar(
            select(models.Constructor).where(
                models.Constructor.id == result.constructor_id
            )
        )
        if not constructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constructor not found",
            )

    existing = db.scalar(
        select(models.RaceResult).where(
            models.RaceResult.race_id == race_id,
            models.RaceResult.driver_id == result.driver_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This driver already has a result for this race",
        )

    new_result = models.RaceResult(race_id=race_id, **result.model_dump())
    db.add(new_result)
    db.flush()
    recalculate_season_history(race.season, db)
    db.commit()
    db.refresh(new_result)
    return new_result


@router.patch(
    "/{race_id}/results/{driver_id}",
    response_model=schemas.RaceResultOut,
)
def update_race_result(
    race_id: int,
    driver_id: int,
    updated: schemas.RaceResultUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Partially update one result. Administrators only."""
    result = db.scalar(
        select(models.RaceResult).where(
            models.RaceResult.race_id == race_id,
            models.RaceResult.driver_id == driver_id,
        )
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race result not found",
        )

    changes = updated.model_dump(exclude_unset=True)
    if "constructor_id" in changes and changes["constructor_id"] is not None:
        constructor = db.scalar(
            select(models.Constructor).where(
                models.Constructor.id == changes["constructor_id"]
            )
        )
        if not constructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constructor not found",
            )

    for field, value in changes.items():
        setattr(result, field, value)

    db.flush()
    recalculate_season_history(result.race.season, db)
    db.commit()
    db.refresh(result)
    return result


@router.delete("/{race_id}/results/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_race_result(
    race_id: int,
    driver_id: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete one result. Administrators only."""
    result = db.scalar(
        select(models.RaceResult).where(
            models.RaceResult.race_id == race_id,
            models.RaceResult.driver_id == driver_id,
        )
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race result not found",
        )

    season = result.race.season
    db.delete(result)
    db.flush()
    recalculate_season_history(season, db)
    db.commit()
