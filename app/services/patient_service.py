# All SQL for patients lives here, so the routes only handle HTTP.
from app import database
from app.schemas.patient import PatientCreate, PatientUpdate

COLUMNS = "id, name, date_of_birth, gender, phone, email, address, blood_group, created_at"


async def get_all_patients(name: str | None = None, limit: int = 20, offset: int = 0):
    # Optional search: ?name=ram matches "Ram", "Ramesh", ... (case-insensitive)
    if name:
        query = f"SELECT {COLUMNS} FROM patients WHERE name ILIKE $1 ORDER BY id LIMIT $2 OFFSET $3"
        rows = await database.pool.fetch(query, f"%{name}%", limit, offset)
    else:
        query = f"SELECT {COLUMNS} FROM patients ORDER BY id LIMIT $1 OFFSET $2"
        rows = await database.pool.fetch(query, limit, offset)
    return [dict(row) for row in rows]


async def get_patient_by_id(patient_id: int):
    query = f"SELECT {COLUMNS} FROM patients WHERE id = $1"
    row = await database.pool.fetchrow(query, patient_id)
    return dict(row) if row else None


async def create_patient(patient: PatientCreate):
    query = f"""
INSERT INTO patients (name, date_of_birth, gender, phone, email, address, blood_group)
VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, patient.name, patient.date_of_birth, patient.gender, patient.phone,
        patient.email, patient.address, patient.blood_group
    )
    return dict(row) if row else None


async def update_patient(patient_id: int, patient: PatientCreate):
    query = f"""
UPDATE patients
SET name = $1, date_of_birth = $2, gender = $3, phone = $4,
    email = $5, address = $6, blood_group = $7
WHERE id = $8
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, patient.name, patient.date_of_birth, patient.gender, patient.phone,
        patient.email, patient.address, patient.blood_group, patient_id
    )
    return dict(row) if row else None


async def patch_patient(patient_id: int, patient: PatientUpdate):
    # COALESCE keeps the old value when a field is not sent (None).
    query = f"""
UPDATE patients
SET name = COALESCE($1, name),
    date_of_birth = COALESCE($2, date_of_birth),
    gender = COALESCE($3, gender),
    phone = COALESCE($4, phone),
    email = COALESCE($5, email),
    address = COALESCE($6, address),
    blood_group = COALESCE($7, blood_group)
WHERE id = $8
RETURNING {COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, patient.name, patient.date_of_birth, patient.gender, patient.phone,
        patient.email, patient.address, patient.blood_group, patient_id
    )
    return dict(row) if row else None


async def delete_patient(patient_id: int):
    query = f"DELETE FROM patients WHERE id = $1 RETURNING {COLUMNS}"
    row = await database.pool.fetchrow(query, patient_id)
    return dict(row) if row else None
