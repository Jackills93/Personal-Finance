import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movement
from app.schemas.movement import MovementCreate, MovementRead, MovementType, MovementUpdate
from app.services import create_movement_and_notify

router = APIRouter(prefix="/movements", tags=["movements"])


@router.get("", response_model=list[MovementRead])
def list_movements(
    type: MovementType | None = None,
    category_id: uuid.UUID | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Movement)
    if type is not None:
        query = query.filter(Movement.type == type)
    if category_id is not None:
        query = query.filter(Movement.category_id == category_id)
    if date_from is not None:
        query = query.filter(Movement.date >= date_from)
    if date_to is not None:
        query = query.filter(Movement.date <= date_to)
    if search:
        query = query.filter(Movement.description.ilike(f"%{search}%"))
    return query.order_by(Movement.date.desc(), Movement.created_at.desc()).all()


@router.post("", response_model=MovementRead, status_code=201)
def create_movement(payload: MovementCreate, db: Session = Depends(get_db)):
    return create_movement_and_notify(db, payload)


@router.patch("/{movement_id}", response_model=MovementRead)
def update_movement(movement_id: uuid.UUID, payload: MovementUpdate, db: Session = Depends(get_db)):
    movement = db.get(Movement, movement_id)
    if movement is None:
        raise HTTPException(status_code=404, detail="Movimento non trovato")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(movement, field, value)
    db.commit()
    db.refresh(movement)
    return movement


@router.delete("/{movement_id}", status_code=204)
def delete_movement(movement_id: uuid.UUID, db: Session = Depends(get_db)):
    movement = db.get(Movement, movement_id)
    if movement is None:
        raise HTTPException(status_code=404, detail="Movimento non trovato")
    db.delete(movement)
    db.commit()
