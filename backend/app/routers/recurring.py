import calendar
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.database import get_db
from app.models import RecurringExpense
from app.schemas.movement import MovementCreate, MovementRead
from app.schemas.recurring import RecurringCreate, RecurringRead, RecurringUpdate
from app.services import create_movement_and_notify

router = APIRouter(prefix="/recurring", tags=["recurring"], dependencies=[Depends(verify_password)])


@router.get("", response_model=list[RecurringRead])
def list_recurring(db: Session = Depends(get_db)):
    return db.query(RecurringExpense).order_by(RecurringExpense.created_at).all()


@router.post("", response_model=RecurringRead, status_code=201)
def create_recurring(payload: RecurringCreate, db: Session = Depends(get_db)):
    recurring = RecurringExpense(**payload.model_dump())
    db.add(recurring)
    db.commit()
    db.refresh(recurring)
    return recurring


@router.patch("/{recurring_id}", response_model=RecurringRead)
def update_recurring(recurring_id: uuid.UUID, payload: RecurringUpdate, db: Session = Depends(get_db)):
    recurring = db.get(RecurringExpense, recurring_id)
    if recurring is None:
        raise HTTPException(status_code=404, detail="Ricorrenza non trovata")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(recurring, field, value)
    db.commit()
    db.refresh(recurring)
    return recurring


@router.delete("/{recurring_id}", status_code=204)
def delete_recurring(recurring_id: uuid.UUID, db: Session = Depends(get_db)):
    recurring = db.get(RecurringExpense, recurring_id)
    if recurring is None:
        raise HTTPException(status_code=404, detail="Ricorrenza non trovata")
    db.delete(recurring)
    db.commit()


def _due_dates(recurring: RecurringExpense, today: date) -> list[date]:
    if recurring.last_generated_date is not None:
        year, month = recurring.last_generated_date.year, recurring.last_generated_date.month
        month += 1
        if month > 12:
            month, year = 1, year + 1
    else:
        year, month = recurring.start_date.year, recurring.start_date.month

    due: list[date] = []
    for _ in range(600):  # bound di sicurezza: 50 anni di mesi
        day = min(recurring.day_of_month, calendar.monthrange(year, month)[1])
        candidate = date(year, month, day)
        if candidate > today:
            break
        if candidate >= recurring.start_date and (recurring.end_date is None or candidate <= recurring.end_date):
            due.append(candidate)
        month += 1
        if month > 12:
            month, year = 1, year + 1
    return due


@router.post("/run-due", response_model=list[MovementRead])
def run_due(db: Session = Depends(get_db)):
    """Genera i movimenti per le occorrenze scadute di ogni ricorrenza attiva.
    Chiamato dal frontend a ogni apertura dell'app (nessun cron esterno)."""
    today = date.today()
    generated = []
    for recurring in db.query(RecurringExpense).filter(RecurringExpense.active.is_(True)).all():
        for occurrence in _due_dates(recurring, today):
            movement = create_movement_and_notify(
                db,
                MovementCreate(
                    type=recurring.type,
                    description=recurring.name,
                    amount=recurring.amount,
                    date=occurrence,
                    category_id=recurring.category_id,
                    account_name=recurring.account_name,
                    person_name=recurring.person_name,
                ),
            )
            generated.append(movement)
            recurring.last_generated_date = occurrence
            db.commit()
    return generated
