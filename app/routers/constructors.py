from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db

router = APIRouter(prefix="/constructors", tags=["constructors"])


@router.post("/", response_model=schemas.ConstructorOut, status_code=status.HTTP_201_CREATED)
def create_constructor(
    constructor: schemas.ConstructorCreate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Create a constructor. Administrators only."""
    new_constructor = models.Constructor(**constructor.model_dump())
    db.add(new_constructor)
    db.commit()
    db.refresh(new_constructor)
    return new_constructor


@router.get("/", response_model=list[schemas.ConstructorOut])
def list_constructors(db: Session = Depends(get_db)):
    """List all constructors."""
    return db.scalars(select(models.Constructor)).all()


@router.get("/{constructor_id}", response_model=schemas.ConstructorOut)
def get_constructor(constructor_id: int, db: Session = Depends(get_db)):
    """Get one constructor by ID."""
    constructor = db.scalar(
        select(models.Constructor).where(models.Constructor.id == constructor_id)
    )
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constructor not found",
        )
    return constructor


@router.patch("/{constructor_id}", response_model=schemas.ConstructorOut)
def update_constructor(
    constructor_id: int,
    updated: schemas.ConstructorUpdate,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Partially update a constructor. Administrators only."""
    constructor = db.scalar(
        select(models.Constructor).where(models.Constructor.id == constructor_id)
    )
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constructor not found",
        )

    for field, value in updated.model_dump(exclude_unset=True).items():
        setattr(constructor, field, value)

    db.commit()
    db.refresh(constructor)
    return constructor


@router.delete("/{constructor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_constructor(
    constructor_id: int,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Delete a constructor without deleting its historical results. Administrators only."""
    constructor = db.scalar(
        select(models.Constructor).where(models.Constructor.id == constructor_id)
    )
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constructor not found",
        )

    db.delete(constructor)
    db.commit()
