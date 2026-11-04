# All SQL for appointments lives here, so the routes only handle HTTP.
from datetime import date
from app import database
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

# Joins patients and doctors so each appointment shows names, not just IDs.
SELECT_WITH_NAMES = """
SELECT a.id, a.appointment_time, a.reason, a.status, a.created_at,
       a.patient_id, p.name AS patient_name,
       a.doctor_id, d.name AS doctor_name, d.specialization
FROM appointments a
JOIN patients p ON p.id = a.patient_id
JOIN doctors d ON d.id = a.doctor_id
"""


async def get_appointments(
    patient_id: int | None = None,
    doctor_id: int | None = None,
    status: str | None = None,
    on_date: date | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    # Builds the WHERE clause only from the filters that were given.
    conditions, values = [], []
    for column, value in [
        ("a.patient_id", patient_id),
        ("a.doctor_id", doctor_id),
        ("a.status", status),
        ("a.appointment_time::DATE", on_date),
    ]:
        if value is not None:
            values.append(value)
            conditions.append(f"{column} = ${len(values)}")

    query = SELECT_WITH_NAMES
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.appointment_time"
    if limit is not None:
        values += [limit, offset]
        query += f" LIMIT ${len(values) - 1} OFFSET ${len(values)}"

    rows = await database.pool.fetch(query, *values)
    return [dict(row) for row in rows]


async def get_appointment_by_id(appointment_id: int):
    row = await database.pool.fetchrow(SELECT_WITH_NAMES + " WHERE a.id = $1", appointment_id)
    return dict(row) if row else None


async def create_appointment(appointment: AppointmentCreate):
    query = """
INSERT INTO appointments (patient_id, doctor_id, appointment_time, reason, status)
VALUES ($1, $2, $3, $4, $5)
RETURNING id
"""
    new_id = await database.pool.fetchval(
        query, appointment.patient_id, appointment.doctor_id,
        appointment.appointment_time, appointment.reason, appointment.status
    )
    return await get_appointment_by_id(new_id)


async def update_appointment(appointment_id: int, appointment: AppointmentCreate):
    query = """
UPDATE appointments
SET patient_id = $1, doctor_id = $2, appointment_time = $3, reason = $4, status = $5
WHERE id = $6
RETURNING id
"""
    updated_id = await database.pool.fetchval(
        query, appointment.patient_id, appointment.doctor_id,
        appointment.appointment_time, appointment.reason, appointment.status,
        appointment_id
    )
    return await get_appointment_by_id(updated_id) if updated_id else None


async def patch_appointment(appointment_id: int, appointment: AppointmentUpdate):
    # COALESCE keeps the old value when a field is not sent (None).
    query = """
UPDATE appointments
SET patient_id = COALESCE($1, patient_id),
    doctor_id = COALESCE($2, doctor_id),
    appointment_time = COALESCE($3, appointment_time),
    reason = COALESCE($4, reason),
    status = COALESCE($5, status)
WHERE id = $6
RETURNING id
"""
    updated_id = await database.pool.fetchval(
        query, appointment.patient_id, appointment.doctor_id,
        appointment.appointment_time, appointment.reason, appointment.status,
        appointment_id
    )
    return await get_appointment_by_id(updated_id) if updated_id else None


async def delete_appointment(appointment_id: int):
    appointment = await get_appointment_by_id(appointment_id)
    if appointment:
        await database.pool.execute("DELETE FROM appointments WHERE id = $1", appointment_id)
    return appointment
