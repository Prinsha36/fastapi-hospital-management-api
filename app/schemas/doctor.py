from typing import Optional
from pydantic import BaseModel


class DoctorCreate(BaseModel):
    # Used for POST and PUT.
    name: str
    specialization: str
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None


class DoctorUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[str] = None
    specialization: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
