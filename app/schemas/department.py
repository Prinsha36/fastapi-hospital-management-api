from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.common import LongText, ShortText


class DepartmentCreate(BaseModel):
    # Used for POST and PUT: both fields are required.
    name: ShortText
    description: LongText


class DepartmentUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[ShortText] = None
    description: Optional[LongText] = None


class DepartmentOut(BaseModel):
    # What the API returns for a department.
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime


class DepartmentDeleted(BaseModel):
    message: str
    department: DepartmentOut
