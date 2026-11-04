# Dependencies that protect routes.
#   Depends(get_current_user) -> must be logged in (any role), else 401
#   Depends(require_admin)    -> must be an admin, else 403
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.services import user_service

# Tells FastAPI (and the Swagger "Authorize" button) where to log in.
# auto_error=False lets us return our own clear message when the token is missing.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not logged in or token expired. Log in at POST /auth/login",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_optional_user(token: str | None = Depends(oauth2_scheme)):
    # Returns the logged-in user, or None if no valid token was sent.
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    return await user_service.get_user_by_username(payload["sub"])


async def get_current_user(user: dict | None = Depends(get_optional_user)):
    if user is None:
        raise UNAUTHORIZED
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user
