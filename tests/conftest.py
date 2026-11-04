# Shared setup for all tests.
#
# Tests use DATABASE_URL from .env, or TEST_DATABASE_URL if you set one.
# Every test creates its own uniquely named records and deletes them afterwards,
# so your existing data is not changed.
import asyncio
import os
import uuid
from datetime import datetime, timedelta

import asyncpg
import pytest
from dotenv import load_dotenv

load_dotenv(".env")
if os.getenv("TEST_DATABASE_URL"):
    # Must be set before the app is imported, because database.py reads it on import.
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def unique(text: str) -> str:
    # Adds a random suffix so tests never clash with real data or each other.
    return f"{text} {uuid.uuid4().hex[:8]}"


def future_time(days: int = 30) -> str:
    return (datetime.now() + timedelta(days=days)).replace(
        hour=10, minute=0, second=0, microsecond=0
    ).isoformat()


@pytest.fixture(scope="session")
def client():
    # On a separate test database, create the tables first.
    if os.getenv("TEST_DATABASE_URL"):
        async def create_tables():
            conn = await asyncpg.connect(os.environ["DATABASE_URL"])
            with open("app/schema.sql") as f:
                await conn.execute(f.read())
            await conn.close()
        asyncio.run(create_tables())

    # "with" runs the app's startup (connect DB) and shutdown (close DB).
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def department(client):
    response = client.post("/departments/", json={
        "name": unique("Test Dept"),
        "description": "Created by tests",
    })
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/departments/{data['id']}")


@pytest.fixture
def doctor(client, department):
    response = client.post("/doctors/", json={
        "name": unique("Dr. Test"),
        "specialization": "Tester",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "department_id": department["id"],
    })
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/doctors/{data['id']}")


@pytest.fixture
def patient(client):
    response = client.post("/patients/", json={
        "name": unique("Test Patient"),
        "date_of_birth": "1990-01-01",
        "gender": "Female",
    })
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/patients/{data['id']}")
