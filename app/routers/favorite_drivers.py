from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_favorite_driver(
        db: Session, user_id: int, driver_id: int) -> models.FavoriteDriver | None:
    """Look up a favorite driver by user and driver. Returns None if it does not exist."""
    return db.scalar(
        select(models.FavoriteDriver).where(
            models.FavoriteDriver.user_id == user_id,
            models.FavoriteDriver.driver_id == driver_id
        )
    )


@router.get("/drivers", response_model=list[schemas.FavoriteDriverOut])
def list_favorite_drivers(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """List every driver favorite by the logged-in user."""
    favorites = db.scalars(
        select(models.FavoriteDriver).where(models.FavoriteDriver.user_id == current_user.id)
    ).all()
    return favorites


@router.post("/drivers", response_model=schemas.FavoriteDriverOut, status_code=status.HTTP_201_CREATED)
def add_favorite_driver(
        payload: schemas.FavoriteDriverCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Add a driver to the logged-in user's favorites."""
    driver = db.scalar(select(models.Driver).where(models.Driver.id == payload.driver_id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    existing = get_favorite_driver(db, current_user.id, payload.driver_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver already in favorites",
        )

    favorite = models.FavoriteDriver(
        user_id=current_user.id,
        driver_id=payload.driver_id
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_driver(
        driver_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Remove a driver from the logged-in user's favorites."""
    favorite = get_favorite_driver(db, current_user.id, driver_id)
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    db.delete(favorite)
    db.commit()
    return None
