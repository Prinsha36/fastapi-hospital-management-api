import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from app.routes.pagination import pagination
from app.core.auth import get_current_user, require_admin
from app.schemas.appointment import AppointmentOut
from app.schemas.doctor import DoctorCreate, DoctorDeleted, DoctorOut, DoctorUpdate
from app.services import doctor_service, appointment_service

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"]
)


async def run_write(action, doctor):
    # Turns database errors into clear HTTP errors.
    try:
        return await action
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"A doctor with email '{doctor.email}' already exists")
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(
            status_code=400,
            detail=f"Department {doctor.department_id} does not exist. Check GET /departments/ for valid IDs"
        )


@router.get("/", response_model=list[DoctorOut])
async def get_doctors(page: dict = Depends(pagination)):
    return await doctor_service.get_all_doctors(**page)


@router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int):
    result = await doctor_service.get_doctor_by_id(doctor_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return result


@router.post("/", response_model=DoctorOut, status_code=201, dependencies=[Depends(get_current_user)])
async def create_doctor(doctor: DoctorCreate):
    result = await run_write(doctor_service.create_doctor(doctor), doctor)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create doctor")
    return result


@router.put("/{doctor_id}", response_model=DoctorOut, dependencies=[Depends(get_current_user)])
async def update_doctor(doctor_id: int, doctor: DoctorCreate):
    result = await run_write(doctor_service.update_doctor(doctor_id, doctor), doctor)
    if result is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return result


@router.patch("/{doctor_id}", response_model=DoctorOut, dependencies=[Depends(get_current_user)])
async def patch_doctor(doctor_id: int, doctor: DoctorUpdate):
    result = await run_write(doctor_service.patch_doctor(doctor_id, doctor), doctor)
    if result is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return result


@router.delete("/{doctor_id}", response_model=DoctorDeleted, dependencies=[Depends(require_admin)])
async def delete_doctor(doctor_id: int):
    result = await doctor_service.delete_doctor(doctor_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {
        "message": "Doctor deleted successfully",
        "doctor": result
    }


@router.get("/{doctor_id}/appointments", response_model=list[AppointmentOut])
async def get_doctor_appointments(doctor_id: int):
    if await doctor_service.get_doctor_by_id(doctor_id) is None:
        raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found")
    return await appointment_service.get_appointments(doctor_id=doctor_id)
