from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.routes.pagination import pagination
from app.core.auth import get_current_user, require_admin
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services import patient_service, appointment_service

router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


@router.get("/")
async def get_patients(name: Optional[str] = None, page: dict = Depends(pagination)):
    # GET /patients/?name=aarav searches by name
    return await patient_service.get_all_patients(name, **page)


@router.get("/{patient_id}")
async def get_patient(patient_id: int):
    result = await patient_service.get_patient_by_id(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return result


@router.post("/", status_code=201, dependencies=[Depends(get_current_user)])
async def create_patient(patient: PatientCreate):
    result = await patient_service.create_patient(patient)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create patient")
    return result


@router.put("/{patient_id}", dependencies=[Depends(get_current_user)])
async def update_patient(patient_id: int, patient: PatientCreate):
    result = await patient_service.update_patient(patient_id, patient)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return result


@router.patch("/{patient_id}", dependencies=[Depends(get_current_user)])
async def patch_patient(patient_id: int, patient: PatientUpdate):
    result = await patient_service.patch_patient(patient_id, patient)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return result


@router.delete("/{patient_id}", dependencies=[Depends(require_admin)])
async def delete_patient(patient_id: int):
    result = await patient_service.delete_patient(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return {
        "message": "Patient deleted successfully",
        "patient": result
    }


@router.get("/{patient_id}/appointments")
async def get_patient_appointments(patient_id: int):
    if await patient_service.get_patient_by_id(patient_id) is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return await appointment_service.get_appointments(patient_id=patient_id)
