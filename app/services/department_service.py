# All SQL for departments lives here, so the routes only handle HTTP.
from app import database
from app.schemas.department import DepartmentCreate, DepartmentUpdate


async def get_all_departments(limit: int = 20, offset: int = 0):
    query = "SELECT * FROM departments ORDER BY id LIMIT $1 OFFSET $2"
    rows = await database.pool.fetch(query, limit, offset)
    return [dict(row) for row in rows]


async def get_department_by_id(department_id: int):
    query = "SELECT * FROM departments WHERE id = $1"
    row = await database.pool.fetchrow(query, department_id)
    return dict(row) if row else None


async def create_department(department: DepartmentCreate):
    query = """
INSERT INTO departments (name, description) VALUES ($1, $2)
RETURNING id, name, description, created_at
"""
    row = await database.pool.fetchrow(query, department.name, department.description)
    return dict(row) if row else None


async def update_department(department_id: int, department: DepartmentCreate):
    query = """
UPDATE departments SET name = $1, description = $2 WHERE id = $3
RETURNING id, name, description, created_at
"""
    row = await database.pool.fetchrow(
        query, department.name, department.description, department_id
    )
    return dict(row) if row else None


async def patch_department(department_id: int, department: DepartmentUpdate):
    # COALESCE keeps the old value when a field is not sent (None).
    query = """
UPDATE departments
SET name = COALESCE($1, name),
    description = COALESCE($2, description)
WHERE id = $3
RETURNING id, name, description, created_at
"""
    row = await database.pool.fetchrow(
        query, department.name, department.description, department_id
    )
    return dict(row) if row else None


async def delete_department(department_id: int):
    query = """
DELETE FROM departments WHERE id = $1
RETURNING id, name, description, created_at
"""
    row = await database.pool.fetchrow(query, department_id)
    return dict(row) if row else None
