# All SQL for emergency cases lives here, so the routes only handle HTTP.
from app import database
from app.schemas.emergency import EmergencyCreate, EmergencyUpdate

# Only doctors in this department can take emergency cases.
EMERGENCY_DEPARTMENT = "Emergency Medicine"

OPEN_STATUSES = ["waiting", "in_treatment"]

# Joins patients and doctors so each case shows names, not just IDs.
# LEFT JOIN because the patient may be unknown and the doctor may not be assigned yet.
# wait_minutes = time since arrival, or how long they waited before treatment started.
SELECT_WITH_NAMES = """
SELECT e.id, e.triage_level, e.status, e.complaint, e.notes,
       e.patient_id, p.name AS patient_name, e.patient_description,
       e.doctor_id, d.name AS doctor_name,
       e.arrived_at, e.treated_at, e.closed_at,
       FLOOR(EXTRACT(EPOCH FROM (COALESCE(e.treated_at, e.closed_at, LOCALTIMESTAMP) - e.arrived_at)) / 60)::INT
           AS wait_minutes
FROM emergency_cases e
LEFT JOIN patients p ON p.id = e.patient_id
LEFT JOIN doctors d ON d.id = e.doctor_id
"""

# Sorts the most serious cases first.
TRIAGE_ORDER = """
CASE e.triage_level
    WHEN 'critical' THEN 1
    WHEN 'urgent' THEN 2
    WHEN 'less_urgent' THEN 3
    ELSE 4
END
"""


async def get_cases(
    status: str | None = None,
    triage_level: str | None = None,
    patient_id: int | None = None,
    doctor_id: int | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    # Builds the WHERE clause only from the filters that were given. Newest first.
    conditions, values = [], []
    for column, value in [
        ("e.status", status),
        ("e.triage_level", triage_level),
        ("e.patient_id", patient_id),
        ("e.doctor_id", doctor_id),
    ]:
        if value is not None:
            values.append(value)
            conditions.append(f"{column} = ${len(values)}")

    query = SELECT_WITH_NAMES
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY e.arrived_at DESC, e.id DESC"
    if limit is not None:
        values += [limit, offset]
        query += f" LIMIT ${len(values) - 1} OFFSET ${len(values)}"

    rows = await database.pool.fetch(query, *values)
    return [dict(row) for row in rows]


async def get_queue(limit: int, offset: int):
    # Waiting patients: most serious first, then whoever arrived first.
    query = SELECT_WITH_NAMES + f"""
WHERE e.status = 'waiting'
ORDER BY {TRIAGE_ORDER}, e.arrived_at, e.id
LIMIT $1 OFFSET $2
"""
    rows = await database.pool.fetch(query, limit, offset)
    return [dict(row) for row in rows]


async def get_case_by_id(case_id: int):
    row = await database.pool.fetchrow(SELECT_WITH_NAMES + " WHERE e.id = $1", case_id)
    return dict(row) if row else None


async def create_case(case: EmergencyCreate):
    query = """
INSERT INTO emergency_cases (patient_id, patient_description, complaint, triage_level)
VALUES ($1, $2, $3, $4)
RETURNING id
"""
    new_id = await database.pool.fetchval(
        query, case.patient_id, case.patient_description, case.complaint, case.triage_level
    )
    return await get_case_by_id(new_id)


async def patch_case(case_id: int, case: EmergencyUpdate):
    # Only open cases can be changed. Returns None if the case is missing or closed.
    query = """
UPDATE emergency_cases
SET patient_id = COALESCE($1, patient_id),
    patient_description = COALESCE($2, patient_description),
    complaint = COALESCE($3, complaint),
    triage_level = COALESCE($4, triage_level)
WHERE id = $5 AND status = ANY($6::text[])
RETURNING id
"""
    updated_id = await database.pool.fetchval(
        query, case.patient_id, case.patient_description, case.complaint, case.triage_level,
        case_id, OPEN_STATUSES
    )
    return await get_case_by_id(updated_id) if updated_id else None


async def get_doctor_department(doctor_id: int):
    # Returns {"id", "department_name"} for the doctor, or None if the doctor doesn't exist.
    row = await database.pool.fetchrow(
        """
SELECT d.id, dep.name AS department_name
FROM doctors d
LEFT JOIN departments dep ON dep.id = d.department_id
WHERE d.id = $1
""",
        doctor_id,
    )
    return dict(row) if row else None


async def assign_doctor(case_id: int, doctor_id: int):
    # Works on waiting cases (starts treatment) and on cases already in treatment
    # (hands over to another doctor). treated_at keeps the first start time.
    query = """
UPDATE emergency_cases
SET doctor_id = $1,
    status = 'in_treatment',
    treated_at = COALESCE(treated_at, LOCALTIMESTAMP)
WHERE id = $2 AND status = ANY($3::text[])
RETURNING id
"""
    updated_id = await database.pool.fetchval(query, doctor_id, case_id, OPEN_STATUSES)
    return await get_case_by_id(updated_id) if updated_id else None


async def close_case(case_id: int, outcome: str, notes: str | None):
    # Only cases in treatment can be closed.
    query = """
UPDATE emergency_cases
SET status = $1, notes = $2, closed_at = LOCALTIMESTAMP
WHERE id = $3 AND status = 'in_treatment'
RETURNING id
"""
    updated_id = await database.pool.fetchval(query, outcome, notes, case_id)
    return await get_case_by_id(updated_id) if updated_id else None


async def delete_case(case_id: int):
    case = await get_case_by_id(case_id)
    if case:
        await database.pool.execute("DELETE FROM emergency_cases WHERE id = $1", case_id)
    return case
