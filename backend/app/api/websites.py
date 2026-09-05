"""Website identification endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import crud
from app.database.database import get_db

router = APIRouter(prefix="/api/websites", tags=["websites"])


@router.get("")
def list_websites(db: Session = Depends(get_db), limit: int = 10):
    return crud.get_websites(db, limit=limit)


@router.get("/top")
def top_websites(db: Session = Depends(get_db), limit: int = 5):
    rows = crud.get_websites(db, limit=limit + 1)
    ranked = sorted(rows, key=lambda r: r.get("bytes", 0) or 0, reverse=True)
    top = ranked[:limit]
    rest = ranked[limit:]
    buckets = [
        {"website": r["website"], "bytes": r.get("bytes", 0), "count": r.get("count", 0)}
        for r in top
    ]
    if rest:
        buckets.append({
            "website": "Other",
            "bytes": sum(r.get("bytes", 0) or 0 for r in rest),
            "count": sum(r.get("count", 0) or 0 for r in rest),
        })
    return buckets