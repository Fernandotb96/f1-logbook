from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/", response_model=schemas.DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    new_driver = models.Driver(**driver.model_dump())
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return new_driver


@router.get("/", response_model=list[schemas.DriverOut])
def list_drivers(db: Session = Depends(get_db)):
    return db.scalars(select(models.Driver)).all()


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
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
):
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
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.scalar(select(models.Driver).where(models.Driver.id == driver_id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    db.delete(driver)
    db.commit()
    return None
