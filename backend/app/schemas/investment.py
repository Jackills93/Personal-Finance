import uuid
from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InvestmentType = Literal["azione", "etf", "obbligazione", "crypto", "altro"]


class InvestmentCreate(BaseModel):
    ticker: str = Field(min_length=1)
    isin: str | None = None
    name: str = Field(min_length=1)
    type: InvestmentType
    sector: str = Field(min_length=1)
    qty: float = Field(gt=0)
    avg_price: float = Field(gt=0)
    cur_price: float = Field(gt=0)


class InvestmentUpdate(BaseModel):
    ticker: str | None = Field(default=None, min_length=1)
    isin: str | None = None
    name: str | None = Field(default=None, min_length=1)
    type: InvestmentType | None = None
    sector: str | None = Field(default=None, min_length=1)
    qty: float | None = Field(default=None, gt=0)
    avg_price: float | None = Field(default=None, gt=0)
    cur_price: float | None = Field(default=None, gt=0)


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticker: str
    isin: str | None
    name: str
    type: InvestmentType
    sector: str
    qty: float
    avg_price: float
    cur_price: float
    added_at: date_type
    updated_at: date_type
