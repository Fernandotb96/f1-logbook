from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth import require_admin
from ...database import get_db
from ...season_history import recalculate_season_history

router = APIRouter(prefix="/races", tags=["sprint results"])


@router.get(
    "/{race_id}/sprint-results",
    response_model=list[schemas.SprintResultOut],
)
def list_sprint_results(race_id: int, db: Session = Depends(get_db)):
    """List the sprint results for one Grand Prix weekend."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    statement = (
        select(models.SprintResult)
        .where(models.SprintResult.race_id == race_id)
        .order_by(models.SprintResult.position, models.SprintResult.id)
    )
    return db.scalars(statement).all()


@router.post(
    "/{race_id}/sprint-results",
    response_model=schemas.SprintResultOut,
    status_code=status.HTTP_201_CREATED,
)
def create_sprint_result(
    race_id: int,
    result: schemas.SprintResultCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Record one driver's sprint result. Administrators only."""
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
        select(models.SprintResult).where(
            models.SprintResult.race_id == race_id,
            models.SprintResult.driver_id == result.driver_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This driver already has a sprint result for this race",
        )

    new_result = models.SprintResult(race_id=race_id, **result.model_dump())
    db.add(new_result)
    db.flush()
    recalculate_season_history(race.season, db)
    db.commit()
    db.refresh(new_result)
    return new_result


@router.patch(
    "/{race_id}/sprint-results/{driver_id}",
    response_model=schemas.SprintResultOut,
)
def update_sprint_result(
    race_id: int,
    driver_id: int,
    updated: schemas.SprintResultUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Partially update one sprint result. Administrators only."""
    result = db.scalar(
        select(models.SprintResult).where(
            models.SprintResult.race_id == race_id,
            models.SprintResult.driver_id == driver_id,
        )
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint result not found",
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


@router.delete(
    "/{race_id}/sprint-results/{driver_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_sprint_result(
    race_id: int,
    driver_id: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete one sprint result. Administrators only."""
    result = db.scalar(
        select(models.SprintResult).where(
            models.SprintResult.race_id == race_id,
            models.SprintResult.driver_id == driver_id,
        )
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint result not found",
        )

    season = result.race.season
    db.delete(result)
    db.flush()
    recalculate_season_history(season, db)
    db.commit()
