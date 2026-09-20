from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db

router = APIRouter(prefix="/races", tags=["races"])


@router.post("/", response_model=schemas.RaceOut, status_code=status.HTTP_201_CREATED)
def create_race(
    race: schemas.RaceCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Create a race. Administrators only."""
    circuit = db.scalar(select(models.Circuit).where(models.Circuit.id == race.circuit_id))
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    existing_race = db.scalar(
        select(models.Race).where(
            models.Race.season == race.season,
            models.Race.round == race.round,
        )
    )
    if existing_race:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A race for this season and round already exists",
        )

    new_race = models.Race(**race.model_dump())
    db.add(new_race)
    db.commit()
    db.refresh(new_race)
    return new_race


@router.get("/", response_model=list[schemas.RaceOut])
def list_races(db: Session = Depends(get_db)):
    """List races from newest season to oldest season."""
    statement = select(models.Race).order_by(models.Race.season.desc(), models.Race.round)
    return db.scalars(statement).all()


@router.get("/{race_id}", response_model=schemas.RaceOut)
def get_race(race_id: int, db: Session = Depends(get_db)):
    """Get one race by ID."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    return race


@router.patch("/{race_id}", response_model=schemas.RaceOut)
def update_race(
    race_id: int,
    updated: schemas.RaceUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Partially update a race. Administrators only."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    changes = updated.model_dump(exclude_unset=True)

    target_circuit_id = changes.get("circuit_id", race.circuit_id)
    target_season = changes.get("season", race.season)
    target_round = changes.get("round", race.round)
    circuit = db.scalar(
        select(models.Circuit).where(models.Circuit.id == target_circuit_id)
    )
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    existing_race = db.scalar(
        select(models.Race).where(
            models.Race.season == target_season,
            models.Race.round == target_round,
            models.Race.id != race.id,
        )
    )
    if existing_race:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A race for this season and round already exists",
        )

    for field, value in changes.items():
        setattr(race, field, value)

    db.commit()
    db.refresh(race)
    return race


@router.delete("/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_race(
    race_id: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete a race and its dependent results and favorites. Administrators only."""
    race = db.scalar(select(models.Race).where(models.Race.id == race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    db.delete(race)
    db.commit()
