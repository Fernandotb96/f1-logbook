from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_favorite_circuit(
    db: Session, user_id: int, circuit_id: int
) -> models.FavoriteCircuit | None:
    """Return a user's favorite circuit if it exists."""
    return db.scalar(
        select(models.FavoriteCircuit).where(
            models.FavoriteCircuit.user_id == user_id,
            models.FavoriteCircuit.circuit_id == circuit_id,
        )
    )


@router.get("/circuits", response_model=list[schemas.FavoriteCircuitOut])
def list_favorite_circuits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List every circuit favorite by the logged-in user."""
    return db.scalars(
        select(models.FavoriteCircuit).where(
            models.FavoriteCircuit.user_id == current_user.id
        )
    ).all()


@router.post(
    "/circuits",
    response_model=schemas.FavoriteCircuitOut,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite_circuit(
    payload: schemas.FavoriteCircuitCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a circuit to the logged-in user's favorites."""
    circuit = db.scalar(select(models.Circuit).where(models.Circuit.id == payload.circuit_id))
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    existing = get_favorite_circuit(db, current_user.id, payload.circuit_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Circuit already in favorites",
        )

    favorite = models.FavoriteCircuit(
        user_id=current_user.id,
        circuit_id=payload.circuit_id,
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.delete("/circuits/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_circuit(
    circuit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a circuit from the logged-in user's favorites."""
    favorite = get_favorite_circuit(db, current_user.id, circuit_id)
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    db.delete(favorite)
    db.commit()
