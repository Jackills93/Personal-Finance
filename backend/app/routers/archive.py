import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.database import get_db
from app.models import Movement

router = APIRouter(prefix="/archive", tags=["archive"], dependencies=[Depends(verify_password)])
logger = logging.getLogger(__name__)


@router.get("/years")
def list_years(db: Session = Depends(get_db)):
    rows = (
        db.query(extract("year", Movement.date).label("year"), func.count().label("count"))
        .group_by("year")
        .order_by("year")
        .all()
    )
    return [{"year": int(r.year), "count": r.count} for r in rows]


@router.get("/{year}")
def export_year(year: int, db: Session = Depends(get_db)):
    movements = db.query(Movement).filter(extract("year", Movement.date) == year).order_by(Movement.date).all()
    if not movements:
        raise HTTPException(status_code=404, detail=f"Nessun movimento per l'anno {year}")
    return [
        {
            "id": str(m.id),
            "type": m.type,
            "description": m.description,
            "amount": float(m.amount),
            "date": m.date.isoformat(),
            "category_id": str(m.category_id) if m.category_id else None,
            "account_name": m.account_name,
            "person_name": m.person_name,
            "from_account_name": m.from_account_name,
            "to_account_name": m.to_account_name,
        }
        for m in movements
    ]


@router.delete("/{year}")
def delete_year(year: int, db: Session = Depends(get_db)):
    deleted = (
        db.query(Movement).filter(extract("year", Movement.date) == year).delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted, "year": year}
