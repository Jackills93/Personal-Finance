from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Movement
from app.schemas.movement import MovementCreate
from app.telegram_client import send_telegram_message


def _month_bounds(d: date) -> tuple[date, date]:
    start = d.replace(day=1)
    end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    return start, end


def create_movement_and_notify(db: Session, payload: MovementCreate) -> Movement:
    movement = Movement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    if movement.type == "expense" and movement.category_id is not None:
        _maybe_notify_limit_exceeded(db, movement)
    return movement


def _maybe_notify_limit_exceeded(db: Session, movement: Movement) -> None:
    category = db.get(Category, movement.category_id)
    if category is None or category.monthly_limit is None:
        return

    month_start, month_end = _month_bounds(movement.date)
    spent_total = db.query(func.coalesce(func.sum(Movement.amount), 0)).filter(
        Movement.type == "expense",
        Movement.category_id == category.id,
        Movement.date >= month_start,
        Movement.date < month_end,
    ).scalar()
    spent_before = float(spent_total) - float(movement.amount)
    limit = float(category.monthly_limit)

    if spent_before <= limit < float(spent_total):
        send_telegram_message(
            f"⚠️ Limite mensile superato per \"{category.name}\": "
            f"{float(spent_total):.2f}€ spesi su {limit:.2f}€ di limite."
        )
