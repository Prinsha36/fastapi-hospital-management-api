# Shared validation rules, reused by every schema.
# If a value breaks a rule, FastAPI returns 422 with a message saying which field and why.
import re
from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BeforeValidator, EmailStr, Field, StringConstraints


# ---------- Text ----------

def text(max_length: int, min_length: int = 1):
    # Trims spaces at both ends, and rejects empty or too-long text.
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)]


Name = text(100, min_length=2)        # e.g. "Dr. Ram Sharma"
ShortText = text(100)                 # e.g. specialization
LongText = text(1000)                 # e.g. description, address, reason


# ---------- Phone ----------

def check_phone(value: str) -> str:
    # Allows spaces, dashes and brackets while typing, then removes them.
    # "+977 980-000-0001" -> "+9779800000001"
    cleaned = re.sub(r"[\s\-()]", "", value)
    if not re.fullmatch(r"\+?\d{7,15}", cleaned):
        raise ValueError("Phone must be 7 to 15 digits, optionally starting with +")
    return cleaned


Phone = Annotated[str, AfterValidator(check_phone)]


# ---------- Email ----------

# EmailStr checks the format (name@domain.com) using the email-validator package.
Email = EmailStr


# ---------- Gender and blood group ----------

def capitalize(value):
    # "male" / "MALE" -> "Male"
    return value.strip().capitalize() if isinstance(value, str) else value


def uppercase(value):
    # "ab+" / " o- " -> "AB+" / "O-"
    return value.strip().upper() if isinstance(value, str) else value


Gender = Annotated[Literal["Male", "Female", "Other"], BeforeValidator(capitalize)]
BloodGroup = Annotated[
    Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    BeforeValidator(uppercase),
]


# ---------- Date of birth ----------

def check_birth_date(value: date) -> date:
    if value > date.today():
        raise ValueError("Date of birth cannot be in the future")
    if value.year < 1900:
        raise ValueError("Date of birth must be after 1900")
    return value


BirthDate = Annotated[date, AfterValidator(check_birth_date)]


# ---------- IDs ----------

# IDs from the database are always positive.
Id = Annotated[int, Field(gt=0)]


# ---------- Login ----------

Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.]+$"),
]
Password = Annotated[str, StringConstraints(min_length=6, max_length=128)]
