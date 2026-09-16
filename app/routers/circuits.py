from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db

router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.post("/", response_model=schemas.CircuitOut, status_code=status.HTTP_201_CREATED)
def create_circuit(
    circuit: schemas.CircuitCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Create a circuit. Administrators only."""
    new_circuit = models.Circuit(**circuit.model_dump())
    db.add(new_circuit)
    db.commit()
    db.refresh(new_circuit)
    return new_circuit


@router.get("/", response_model=list[schemas.CircuitOut])
def list_circuits(db: Session = Depends(get_db)):
    """List all circuits."""
    return db.scalars(select(models.Circuit)).all()


@router.get("/{circuit_id}", response_model=schemas.CircuitOut)
def get_circuit(circuit_id: int, db: Session = Depends(get_db)):
    """Get one circuit by ID."""
    circuit = db.scalar(select(models.Circuit).where(models.Circuit.id == circuit_id))
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    return circuit


@router.patch("/{circuit_id}", response_model=schemas.CircuitOut)
def update_circuit(
    circuit_id: int,
    updated: schemas.CircuitUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Partially update a circuit. Administrators only."""
    circuit = db.scalar(select(models.Circuit).where(models.Circuit.id == circuit_id))
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    for field, value in updated.model_dump(exclude_unset=True).items():
        setattr(circuit, field, value)

    db.commit()
    db.refresh(circuit)
    return circuit


@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete a circuit. Administrators only."""
    circuit = db.scalar(select(models.Circuit).where(models.Circuit.id == circuit_id))
    if not circuit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    db.delete(circuit)
    db.commit()
