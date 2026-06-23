import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.database import get_db
from app.models import Person
from app.schemas.person import PersonCreate, PersonRead, PersonUpdate

router = APIRouter(prefix="/persons", tags=["persons"], dependencies=[Depends(verify_password)])


@router.get("", response_model=list[PersonRead])
def list_persons(db: Session = Depends(get_db)):
    return db.query(Person).order_by(Person.created_at).all()


@router.post("", response_model=PersonRead, status_code=201)
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    person = Person(**payload.model_dump())
    db.add(person)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Persona già presente") from None
    db.refresh(person)
    return person


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(person_id: uuid.UUID, payload: PersonUpdate, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    person.name = payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Persona già presente") from None
    db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: uuid.UUID, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    db.delete(person)
    db.commit()
