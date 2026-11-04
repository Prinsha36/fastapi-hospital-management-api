from typing import Optional
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    # Used for POST and PUT: both fields are required.
    name: str
    description: str


class DepartmentUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[str] = None
    description: Optional[str] = None
