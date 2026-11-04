from datetime import date
from typing import Optional
from pydantic import BaseModel


class PatientCreate(BaseModel):
    # Used for POST and PUT. Only name is required.
    name: str
    date_of_birth: Optional[date] = None   # Format: "YYYY-MM-DD"
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None


class PatientUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
