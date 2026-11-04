import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from app.routes.pagination import pagination
from app.core.auth import get_current_user, require_admin
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services import department_service, doctor_service

# prefix="/departments": every endpoint here starts with /departments.
# tags: groups these endpoints in the Swagger docs.
router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.get("/")
async def get_departments(page: dict = Depends(pagination)):
    return await department_service.get_all_departments(**page)


@router.get("/{department_id}")
async def get_department(department_id: int):
    result = await department_service.get_department_by_id(department_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return result


@router.post("/", status_code=201, dependencies=[Depends(get_current_user)])
async def create_department(department: DepartmentCreate):
    try:
        result = await department_service.create_department(department)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Department '{department.name}' already exists")
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create department")
    return result


@router.put("/{department_id}", dependencies=[Depends(get_current_user)])
async def update_department(department_id: int, department: DepartmentCreate):
    try:
        result = await department_service.update_department(department_id, department)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Department '{department.name}' already exists")
    if result is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return result


@router.patch("/{department_id}", dependencies=[Depends(get_current_user)])
async def patch_department(department_id: int, department: DepartmentUpdate):
    try:
        result = await department_service.patch_department(department_id, department)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Department '{department.name}' already exists")
    if result is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return result


@router.delete("/{department_id}", dependencies=[Depends(require_admin)])
async def delete_department(department_id: int):
    result = await department_service.delete_department(department_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return {
        "message": "Department deleted successfully",
        "department": result
    }


@router.get("/{department_id}/doctors")
async def get_department_doctors(department_id: int):
    department = await department_service.get_department_by_id(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return await doctor_service.get_doctors_by_department(department_id)
