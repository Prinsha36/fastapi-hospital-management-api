from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Role = Literal["admin", "staff"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
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
