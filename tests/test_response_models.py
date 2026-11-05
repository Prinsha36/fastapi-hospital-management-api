# Checks that every response matches its response model exactly:
# no missing fields, no extra fields (like a password hash), right types.
import pytest

from app.main import app
from app.schemas.appointment import AppointmentOut
from app.schemas.department import DepartmentOut
from app.schemas.doctor import DoctorOut
from app.schemas.emergency import EmergencyCaseOut
from app.schemas.patient import PatientOut
from app.schemas.user import UserOut
from tests.conftest import future_time, unique


def assert_shape(data: dict, model):
    # Same field names as the model, and every value passes the model's types.
    assert set(data) == set(model.model_fields), f"{model.__name__} fields differ"
    model.model_validate(data)


def test_every_endpoint_documents_its_response():
    # Swagger should show a response body for every endpoint, never an empty {}.
    missing = []
    for path, methods in app.openapi()["paths"].items():
        for method, operation in methods.items():
            success = next(code for code in operation["responses"] if code.startswith("2"))
            schema = operation["responses"][success].get("content", {}).get("application/json", {}).get("schema")
            if not schema:
                missing.append(f"{method.upper()} {path}")
    assert missing == []


def test_department_shape(client, department):
    assert_shape(department, DepartmentOut)
    assert_shape(client.get(f"/departments/{department['id']}").json(), DepartmentOut)
    for row in client.get("/departments/").json():
        assert_shape(row, DepartmentOut)


def test_doctor_shape(client, doctor, department):
    assert_shape(doctor, DoctorOut)
    assert_shape(client.get(f"/doctors/{doctor['id']}").json(), DoctorOut)
    for row in client.get(f"/departments/{department['id']}/doctors").json():
        assert_shape(row, DoctorOut)


def test_patient_shape(client, patient):
    assert_shape(patient, PatientOut)
    assert_shape(client.get(f"/patients/{patient['id']}").json(), PatientOut)


def test_appointment_shape(client, patient, doctor):
    created = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(days=50),
    }).json()
    assert_shape(created, AppointmentOut)
    for row in client.get(f"/patients/{patient['id']}/appointments").json():
        assert_shape(row, AppointmentOut)

    deleted = client.delete(f"/appointments/{created['id']}").json()
    assert set(deleted) == {"message", "appointment"}
    assert_shape(deleted["appointment"], AppointmentOut)


def test_emergency_shape(client):
    created = client.post("/emergency/", json={
        "patient_description": "Shape test", "complaint": "Fall", "triage_level": "urgent",
    }).json()
    assert_shape(created, EmergencyCaseOut)
    for row in client.get("/emergency/queue").json():
        assert_shape(row, EmergencyCaseOut)

    deleted = client.delete(f"/emergency/{created['id']}").json()
    assert set(deleted) == {"message", "emergency_case"}
    assert_shape(deleted["emergency_case"], EmergencyCaseOut)


@pytest.mark.parametrize("path, body, key, model", [
    ("/departments/", {"name": unique("Shape Dept"), "description": "Temporary"}, "department", DepartmentOut),
    ("/patients/", {"name": unique("Shape Patient")}, "patient", PatientOut),
])
def test_delete_response_shape(client, path, body, key, model):
    created = client.post(path, json=body).json()
    deleted = client.delete(f"{path}{created['id']}").json()
    assert set(deleted) == {"message", key}
    assert_shape(deleted[key], model)


def test_me_never_returns_password(client):
    data = client.get("/auth/me").json()
    assert_shape(data, UserOut)
    assert "hashed_password" not in data
