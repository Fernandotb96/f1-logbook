import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import require_admin
from ..database import get_db
from ..sync import JolpicaSyncError, sync_season


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/{year}", response_model=schemas.SeasonSyncOut)
def synchronize_season(
    year: int,
    completed: Optional[bool] = None,
    db: Session = Depends(get_db),
    _current_admin: models.User = Depends(require_admin),
):
    """Synchronize one season from Jolpica. Administrators only."""
    try:
        summary = sync_season(year, db, completed=completed)
        db.commit()
        return summary
    except JolpicaSyncError as error:
        db.rollback()
        logger.warning("Jolpica sync failed for season %s: %s", year, error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except Exception as error:
        db.rollback()
        logger.exception("Unexpected error while synchronizing season %s", year)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not synchronize the season",
        ) from error
