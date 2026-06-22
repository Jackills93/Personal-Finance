import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RecurringType = Literal["income", "expense"]


class RecurringCreate(BaseModel):
    name: str = Field(min_length=1)
    type: RecurringType = "expense"
    amount: float = Field(gt=0)
    category_id: uuid.UUID | None = None
    account_name: str | None = None
    person_name: str | None = None
    day_of_month: int = Field(ge=1, le=31)
    start_date: date_type
    end_date: date_type | None = None
    active: bool = True


class RecurringUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    type: RecurringType | None = None
    amount: float | None = Field(default=None, gt=0)
    category_id: uuid.UUID | None = None
    account_name: str | None = None
    person_name: str | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    start_date: date_type | None = None
    end_date: date_type | None = None
    active: bool | None = None


class RecurringRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: RecurringType
    amount: float
    category_id: uuid.UUID | None
    account_name: str | None
    person_name: str | None
    day_of_month: int
    start_date: date_type
    end_date: date_type | None
    active: bool
    last_generated_date: date_type | None
    created_at: datetime
