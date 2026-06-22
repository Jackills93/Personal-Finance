import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MovementType = Literal["income", "expense", "transfer"]


class MovementCreate(BaseModel):
    type: MovementType
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date: date_type
    category_id: uuid.UUID | None = None
    account_name: str | None = None
    person_name: str | None = None
    from_account_name: str | None = None
    to_account_name: str | None = None
    goal_name: str | None = None
    goal_amount: float | None = Field(default=None, ge=0)


class MovementUpdate(BaseModel):
    type: MovementType | None = None
    description: str | None = Field(default=None, min_length=1)
    amount: float | None = Field(default=None, gt=0)
    date: date_type | None = None
    category_id: uuid.UUID | None = None
    account_name: str | None = None
    person_name: str | None = None
    from_account_name: str | None = None
    to_account_name: str | None = None
    goal_name: str | None = None
    goal_amount: float | None = Field(default=None, ge=0)


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: MovementType
    description: str
    amount: float
    date: date_type
    category_id: uuid.UUID | None
    account_name: str | None
    person_name: str | None
    from_account_name: str | None
    to_account_name: str | None
    goal_name: str | None
    goal_amount: float | None
    created_at: datetime
