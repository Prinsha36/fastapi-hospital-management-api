from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.common import Email, Id, Name, Phone, ShortText


class DoctorCreate(BaseModel):
    # Used for POST and PUT.
    name: Name
    specialization: ShortText
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    department_id: Optional[Id] = None


class DoctorUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[Name] = None
    specialization: Optional[ShortText] = None
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    department_id: Optional[Id] = None


class DoctorOut(BaseModel):
    # What the API returns for a doctor.
    id: int
    name: str
    specialization: str
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    created_at: datetime


class DoctorDeleted(BaseModel):
    message: str
    doctor: DoctorOut
