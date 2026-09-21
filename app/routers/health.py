import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("readiness_check_failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable") from None
    return {"status": "ready"}
