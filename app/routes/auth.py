import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import get_current_user, get_optional_user, require_admin
from app.core.security import create_access_token, verify_password
from app.schemas.user import Token, UserCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate, current_user: dict | None = Depends(get_optional_user)):
    # The very first account can be created by anyone and becomes an admin.
    # After that, only a logged-in admin can create accounts.
    if await user_service.count_users() == 0:
        role = "admin"
    elif current_user is None:
        raise HTTPException(status_code=401, detail="Log in as an admin to create users")
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")
    else:
        role = user.role

    try:
        return await user_service.create_user(user, role)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Username '{user.username}' is already taken")


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # Sent as a form (username + password), which is what the Swagger
    # "Authorize" button uses.
    user = await user_service.get_user_by_username(form.username, include_password=True)
    if user is None or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    return {"access_token": create_access_token(user["username"], user["role"])}


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
async def list_users(_: dict = Depends(require_admin)):
    return await user_service.get_all_users()


@router.delete("/users/{user_id}", response_model=UserOut)
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    result = await user_service.delete_user(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return result
