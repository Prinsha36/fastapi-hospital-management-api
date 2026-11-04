# All SQL for doctors lives here, so the routes only handle HTTP.
from app import database
from app.schemas.doctor import DoctorCreate, DoctorUpdate

COLUMNS = "id, name, specialization, phone, email, department_id, created_at"


async def get_all_doctors(limit: int = 20, offset: int = 0):
    query = f"SELECT {COLUMNS} FROM doctors ORDER BY id LIMIT $1 OFFSET $2"
    rows = await database.pool.fetch(query, limit, offset)
    return [dict(row) for row in rows]


async def get_doctor_by_id(doctor_id: int):
    query = f"SELECT {COLUMNS} FROM doctors WHERE id = $1"
    row = await database.pool.fetchrow(query, doctor_id)
    return dict(row) if row else None


async def get_doctors_by_department(department_id: int):
    query = f"SELECT {COLUMNS} FROM doctors WHERE department_id = $1 ORDER BY id"
    rows = await database.pool.fetch(query, department_id)
    return [dict(row) for row in rows]


async def create_doctor(doctor: DoctorCreate):
    query = f"""
INSERT INTO doctors (name, specialization, phone, email, department_id)
VALUES ($1, $2, $3, $4, $5)
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, doctor.name, doctor.specialization, doctor.phone,
        doctor.email, doctor.department_id
    )
    return dict(row) if row else None


async def update_doctor(doctor_id: int, doctor: DoctorCreate):
    query = f"""
UPDATE doctors
SET name = $1, specialization = $2, phone = $3, email = $4, department_id = $5
WHERE id = $6
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, doctor.name, doctor.specialization, doctor.phone,
        doctor.email, doctor.department_id, doctor_id
    )
    return dict(row) if row else None


async def patch_doctor(doctor_id: int, doctor: DoctorUpdate):
    # COALESCE keeps the old value when a field is not sent (None).
    query = f"""
UPDATE doctors
SET name = COALESCE($1, name),
    specialization = COALESCE($2, specialization),
    phone = COALESCE($3, phone),
    email = COALESCE($4, email),
    department_id = COALESCE($5, department_id)
WHERE id = $6
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, doctor.name, doctor.specialization, doctor.phone,
        doctor.email, doctor.department_id, doctor_id
    )
    return dict(row) if row else None


async def delete_doctor(doctor_id: int):
    query = f"DELETE FROM doctors WHERE id = $1 RETURNING {COLUMNS}"
    row = await database.pool.fetchrow(query, doctor_id)
    return dict(row) if row else None
