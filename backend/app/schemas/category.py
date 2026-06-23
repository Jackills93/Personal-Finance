import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CategoryType = Literal["income", "expense"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    type: CategoryType = "expense"
    color: str = "#7CA8E3"
    monthly_limit: float | None = Field(default=None, ge=0)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    type: CategoryType | None = None
    color: str | None = None
    monthly_limit: float | None = Field(default=None, ge=0)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: CategoryType
    color: str
    monthly_limit: float | None
    created_at: datetime
