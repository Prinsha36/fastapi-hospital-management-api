from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel
from app.schemas.common import Id, LongText

# The only allowed values for status. Anything else gives a 422 error.
Status = Literal["scheduled", "completed", "cancelled"]


class AppointmentCreate(BaseModel):
    # Used for POST and PUT.
    patient_id: Id
    doctor_id: Id
    appointment_time: datetime   # Format: "YYYY-MM-DDTHH:MM", e.g. "2026-11-10T10:30"
    reason: Optional[LongText] = None
    status: Status = "scheduled"


class AppointmentUpdate(BaseModel):
    # Used for PATCH: send only the fields you want to change.
    # Example: {"status": "cancelled"} to cancel an appointment.
    patient_id: Optional[Id] = None
    doctor_id: Optional[Id] = None
    appointment_time: Optional[datetime] = None
    reason: Optional[LongText] = None
    status: Optional[Status] = None
