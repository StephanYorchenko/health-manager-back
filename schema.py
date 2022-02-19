import enum
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Optional[str] = Field(None)
    login: str = Field(...)
    fullName: Optional[str] = Field(None)


class RoomDTO(BaseModel):
    name: str
    identifier: int


class Categories(enum.Enum):
    begin = 0
    stop = 1
    keep = 2
