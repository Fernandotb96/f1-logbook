from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_favorite_race(
    db: Session, user_id: int, race_id: int
) -> models.FavoriteRace | None:
    """Return a user's favorite race if it exists."""
    return db.scalar(
        select(models.FavoriteRace).where(
            models.FavoriteRace.user_id == user_id,
            models.FavoriteRace.race_id == race_id,
        )
    )


@router.get("/races", response_model=list[schemas.FavoriteRaceOut])
def list_favorite_races(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List every race favorite by the logged-in user."""
    return db.scalars(
        select(models.FavoriteRace).where(
            models.FavoriteRace.user_id == current_user.id
        )
    ).all()


@router.post(
    "/races",
    response_model=schemas.FavoriteRaceOut,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite_race(
    payload: schemas.FavoriteRaceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a race to the logged-in user's favorites."""
    race = db.scalar(select(models.Race).where(models.Race.id == payload.race_id))
    if not race:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    existing = get_favorite_race(db, current_user.id, payload.race_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Race already in favorites",
        )

    favorite = models.FavoriteRace(user_id=current_user.id, race_id=payload.race_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.delete("/races/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_race(
    race_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a race from the logged-in user's favorites."""
    favorite = get_favorite_race(db, current_user.id, race_id)
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    db.delete(favorite)
    db.commit()
