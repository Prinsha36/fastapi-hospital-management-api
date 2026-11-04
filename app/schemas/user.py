from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel
from app.schemas.common import Name, Password, Username

Role = Literal["admin", "staff"]


class UserCreate(BaseModel):
    username: Username          # letters, numbers, _ and . only
    password: Password          # 6 to 128 characters
    full_name: Optional[Name] = None
    role: Role = "staff"


class UserOut(BaseModel):
    # What the API returns about a user. The password hash is never included.
    id: int
    username: str
    full_name: Optional[str] = None
    role: Role
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
