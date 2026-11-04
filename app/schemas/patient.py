from typing import Optional
from pydantic import BaseModel
from app.schemas.common import BirthDate, BloodGroup, Email, Gender, LongText, Name, Phone


class PatientCreate(BaseModel):
    # Used for POST and PUT. Only name is required.
    name: Name
    date_of_birth: Optional[BirthDate] = None   # Format: "YYYY-MM-DD"
    gender: Optional[Gender] = None             # Male, Female or Other
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    address: Optional[LongText] = None
    blood_group: Optional[BloodGroup] = None    # A+, A-, B+, B-, AB+, AB-, O+, O-


class PatientUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    name: Optional[Name] = None
    date_of_birth: Optional[BirthDate] = None
    gender: Optional[Gender] = None
    phone: Optional[Phone] = None
    email: Optional[Email] = None
    address: Optional[LongText] = None
    blood_group: Optional[BloodGroup] = None
