import uuid
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=1)
    target: float = Field(gt=0)
    current: float = Field(default=0, ge=0)
    deadline: date_type | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    target: float | None = Field(default=None, gt=0)
    current: float | None = Field(default=None, ge=0)
    deadline: date_type | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    target: float
    current: float
    deadline: date_type | None
    created_at: datetime
