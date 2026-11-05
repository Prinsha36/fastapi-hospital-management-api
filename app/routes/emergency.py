from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from app.routes.pagination import pagination
from app.core.auth import get_current_user, require_admin
from app.schemas.emergency import (
    CaseStatus, EmergencyAssign, EmergencyCaseDeleted, EmergencyCaseOut, EmergencyClose,
    EmergencyCreate, EmergencyUpdate, TriageLevel,
)
from app.services import emergency_service
from app.services.emergency_service import EMERGENCY_DEPARTMENT

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency"]
)


async def run_write(action, patient_id: int | None):
    # Turns database errors into clear HTTP errors.
    try:
        return await action
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=409, detail=f"Patient {patient_id} already has an open emergency case"
        )
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=400, detail=f"Patient {patient_id} does not exist")


async def explain_failed_change(case_id: int, action: str):
    # Called when an UPDATE matched nothing: either the case is missing (404)
    # or it is in the wrong status for this action (409).
    case = await emergency_service.get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Emergency case {case_id} not found")
    raise HTTPException(
        status_code=409,
        detail=f"Cannot {action} emergency case {case_id} because its status is '{case['status']}'"
    )


@router.get("/", response_model=list[EmergencyCaseOut])
async def get_cases(
    status: Optional[CaseStatus] = None,
    triage_level: Optional[TriageLevel] = None,
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    page: dict = Depends(pagination),
):
    # All cases, newest first. Filters are optional, e.g. /emergency/?status=admitted
    return await emergency_service.get_cases(status, triage_level, patient_id, doctor_id, **page)


@router.get("/queue", response_model=list[EmergencyCaseOut])
async def get_queue(page: dict = Depends(pagination)):
    # Patients waiting to be seen: critical first, then by arrival time.
    return await emergency_service.get_queue(**page)


@router.get("/{case_id}", response_model=EmergencyCaseOut)
async def get_case(case_id: int):
    result = await emergency_service.get_case_by_id(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Emergency case {case_id} not found")
    return result


@router.post("/", response_model=EmergencyCaseOut, status_code=201, dependencies=[Depends(get_current_user)])
async def create_case(case: EmergencyCreate):
    # Registers a patient arriving at the emergency department.
    return await run_write(emergency_service.create_case(case), case.patient_id)


@router.patch("/{case_id}", response_model=EmergencyCaseOut, dependencies=[Depends(get_current_user)])
async def patch_case(case_id: int, case: EmergencyUpdate):
    # Change triage level, complaint or patient while the case is still open.
    result = await run_write(emergency_service.patch_case(case_id, case), case.patient_id)
    if result is None:
        await explain_failed_change(case_id, "update")
    return result


@router.patch("/{case_id}/assign", response_model=EmergencyCaseOut, dependencies=[Depends(get_current_user)])
async def assign_doctor(case_id: int, body: EmergencyAssign):
    # Gives the case to a doctor and starts treatment.
    if await emergency_service.get_case_by_id(case_id) is None:
        raise HTTPException(status_code=404, detail=f"Emergency case {case_id} not found")

    doctor =await emergency_service.get_doctor_department(body.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=400, detail=f"Doctor {body.doctor_id} does not exist")
    if doctor["department_name"] != EMERGENCY_DEPARTMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor {body.doctor_id} is not in the {EMERGENCY_DEPARTMENT} department"
        )

    result = await emergency_service.assign_doctor(case_id, body.doctor_id)
    if result is None:
        await explain_failed_change(case_id, "assign a doctor to")
    return result


@router.patch("/{case_id}/close", response_model=EmergencyCaseOut, dependencies=[Depends(get_current_user)])
async def close_case(case_id: int, body: EmergencyClose):
    # Ends treatment: the patient is discharged, admitted or transferred.
    result = await emergency_service.close_case(case_id, body.outcome, body.notes)
    if result is None:
        await explain_failed_change(case_id, "close")
    return result


@router.delete("/{case_id}", response_model=EmergencyCaseDeleted, dependencies=[Depends(require_admin)])
async def delete_case(case_id: int):
    result = await emergency_service.delete_case(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Emergency case {case_id} not found")
    return {
        "message": "Emergency case deleted successfully",
        "emergency_case": result
    }
