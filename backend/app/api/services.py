"""Service identification endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analysis.service_identifier import top_service_buckets
from app.database import crud
from app.database.database import get_db

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("")
def list_services(db: Session = Depends(get_db), limit: int = 20):
    return crud.get_services(db, limit=limit)


@router.get("/top")
def top_services(db: Session = Depends(get_db), limit: int = 5):
    services = crud.get_services(db, limit=limit + 1)
    return top_service_buckets(services, max_buckets=limit)