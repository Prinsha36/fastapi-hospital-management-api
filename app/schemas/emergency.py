from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, model_validator
from app.schemas.common import Id, LongText

# How serious the case is. The queue shows "critical" first.
TriageLevel = Literal["critical", "urgent", "less_urgent", "non_urgent"]

# How a case ends.
Outcome = Literal["discharged", "admitted", "transferred"]

# Every status a case can have:
#   waiting -> in_treatment -> discharged / admitted / transferred
CaseStatus = Literal["waiting", "in_treatment", "discharged", "admitted", "transferred"]


class EmergencyCreate(BaseModel):
    # Send patient_id for a known patient.
    # For an unknown patient (e.g. unconscious), leave it out and send patient_description.
    patient_id: Optional[Id] = None
    patient_description: Optional[LongText] = None   # e.g. "Unknown male, around 30"
    complaint: LongText                              # e.g. "Chest pain"
    triage_level: TriageLevel

    @model_validator(mode="after")
    def patient_or_description(self):
        if self.patient_id is None and self.patient_description is None:
            raise ValueError("Send patient_id, or patient_description if the patient is unknown")
        return self


class EmergencyUpdate(BaseModel):
    # Used for PATCH on an open case: send only the fields you want to change.
    # Example: {"triage_level": "critical"} when the patient gets worse,
    # or {"patient_id": 12} once an unknown patient is identified.
    patient_id: Optional[Id] = None
    patient_description: Optional[LongText] = None
    complaint: Optional[LongText] = None
    triage_level: Optional[TriageLevel] = None


class EmergencyAssign(BaseModel):
    doctor_id: Id


class EmergencyClose(BaseModel):
    outcome: Outcome
    notes: Optional[LongText] = None   # e.g. "Stitched, follow up in 1 week"


class EmergencyCaseOut(BaseModel):
    # What the API returns for an emergency case.
    id: int
    triage_level: TriageLevel
    status: CaseStatus
    complaint: str
    notes: Optional[str] = None
    patient_id: Optional[int] = None        # Empty for an unknown patient
    patient_name: Optional[str] = None
    patient_description: Optional[str] = None
    doctor_id: Optional[int] = None         # Empty until a doctor is assigned
    doctor_name: Optional[str] = None
    arrived_at: datetime
    treated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    wait_minutes: int                       # Minutes waited before treatment (or so far)


class EmergencyCaseDeleted(BaseModel):
    message: str
    emergency_case: EmergencyCaseOut
