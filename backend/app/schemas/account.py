import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AccountType = Literal["corrente", "risparmio", "investimento", "contanti", "carta"]


class AccountCreate(BaseModel):
    name: str = Field(min_length=1)
    type: AccountType
    initial_balance: float = 0
    color: str = "#6FE3A0"


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    type: AccountType | None = None
    initial_balance: float | None = None
    color: str | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: AccountType
    initial_balance: float
    color: str
    created_at: datetime
