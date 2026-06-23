import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonCreate(BaseModel):
    name: str = Field(min_length=1)


class PersonUpdate(BaseModel):
    name: str = Field(min_length=1)


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
