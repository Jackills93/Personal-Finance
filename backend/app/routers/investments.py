import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.database import get_db
from app.models import Investment
from app.schemas.investment import InvestmentCreate, InvestmentRead, InvestmentUpdate

router = APIRouter(prefix="/investments", tags=["investments"], dependencies=[Depends(verify_password)])


@router.get("", response_model=list[InvestmentRead])
def list_investments(db: Session = Depends(get_db)):
    return db.query(Investment).order_by(Investment.added_at).all()


@router.post("", response_model=InvestmentRead, status_code=201)
def create_investment(payload: InvestmentCreate, db: Session = Depends(get_db)):
    today = date.today()
    investment = Investment(**payload.model_dump(), added_at=today, updated_at=today)
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return investment


@router.patch("/{investment_id}", response_model=InvestmentRead)
def update_investment(investment_id: uuid.UUID, payload: InvestmentUpdate, db: Session = Depends(get_db)):
    investment = db.get(Investment, investment_id)
    if investment is None:
        raise HTTPException(status_code=404, detail="Investimento non trovato")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(investment, field, value)
    investment.updated_at = date.today()
    db.commit()
    db.refresh(investment)
    return investment


@router.delete("/{investment_id}", status_code=204)
def delete_investment(investment_id: uuid.UUID, db: Session = Depends(get_db)):
    investment = db.get(Investment, investment_id)
    if investment is None:
        raise HTTPException(status_code=404, detail="Investimento non trovato")
    db.delete(investment)
    db.commit()
