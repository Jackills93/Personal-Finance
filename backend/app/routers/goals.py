import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.database import get_db
from app.models import Goal
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"], dependencies=[Depends(verify_password)])


@router.get("", response_model=list[GoalRead])
def list_goals(db: Session = Depends(get_db)):
    return db.query(Goal).order_by(Goal.created_at).all()


@router.post("", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: uuid.UUID, payload: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Obiettivo non trovato")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: uuid.UUID, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Obiettivo non trovato")
    db.delete(goal)
    db.commit()
