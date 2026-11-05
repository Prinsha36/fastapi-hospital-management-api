from datetime import date, datetime
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from app.routes.pagination import pagination
from app.core.auth import get_current_user, require_admin
from app.schemas.appointment import (
    AppointmentCreate, AppointmentDeleted, AppointmentOut, AppointmentUpdate, Status,
)
from app.services import appointment_service

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def check_time(appointment_time: datetime | None) -> datetime | None:
    # Stores times as local time without a timezone, and blocks past bookings.
    if appointment_time is None:
        return None
    if appointment_time.tzinfo is not None:
        appointment_time = appointment_time.astimezone().replace(tzinfo=None)
    if appointment_time < datetime.now():
        raise HTTPException(status_code=400, detail="Appointment time cannot be in the past")
    return appointment_time


async def run_write(action, appointment):
    # Turns database errors into clear HTTP errors.
    try:
        return await action
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=409,
            detail=f"Doctor {appointment.doctor_id} already has an appointment at {appointment.appointment_time}"
        )
    except asyncpg.ForeignKeyViolationError as e:
        if "patient" in (e.constraint_name or ""):
            detail = f"Patient {appointment.patient_id} does not exist"
        else:
            detail = f"Doctor {appointment.doctor_id} does not exist"
        raise HTTPException(status_code=400, detail=detail)


@router.get("/", response_model=list[AppointmentOut])
async def get_appointments(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[Status] = None,
    date: Optional[date] = None,
    page: dict = Depends(pagination),
):
    # All filters are optional, e.g. /appointments/?doctor_id=8&date=2026-11-05&limit=10
    return await appointment_service.get_appointments(patient_id, doctor_id, status, date, **page)


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(appointment_id: int):
    result = await appointment_service.get_appointment_by_id(appointment_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return result


@router.post("/", response_model=AppointmentOut, status_code=201, dependencies=[Depends(get_current_user)])
async def create_appointment(appointment: AppointmentCreate):
    appointment.appointment_time = check_time(appointment.appointment_time)
    return await run_write(appointment_service.create_appointment(appointment), appointment)


@router.put("/{appointment_id}", response_model=AppointmentOut, dependencies=[Depends(get_current_user)])
async def update_appointment(appointment_id: int, appointment: AppointmentCreate):
    appointment.appointment_time = check_time(appointment.appointment_time)
    result = await run_write(
        appointment_service.update_appointment(appointment_id, appointment), appointment
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return result


@router.patch("/{appointment_id}", response_model=AppointmentOut, dependencies=[Depends(get_current_user)])
async def patch_appointment(appointment_id: int, appointment: AppointmentUpdate):
    appointment.appointment_time = check_time(appointment.appointment_time)
    result = await run_write(
        appointment_service.patch_appointment(appointment_id, appointment), appointment
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return result


@router.delete("/{appointment_id}", response_model=AppointmentDeleted, dependencies=[Depends(require_admin)])
async def delete_appointment(appointment_id: int):
    result = await appointment_service.delete_appointment(appointment_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return {
        "message": "Appointment deleted successfully",
        "appointment": result
    }
