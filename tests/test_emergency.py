import uuid

import pytest
from tests.conftest import NO_AUTH, unique


@pytest.fixture
def emergency_doctor(client):
    # A doctor in the "Emergency Medicine" department (created by schema.sql).
    departments = client.get("/departments/?limit=100").json()
    department = next(d for d in departments if d["name"] == "Emergency Medicine")
    response = client.post("/doctors/", json={
        "name": unique("Dr. Emergency"),
        "specialization": "Emergency Physician",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "department_id": department["id"],
    })
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/doctors/{data['id']}")


@pytest.fixture
def new_case(client):
    # Call new_case(...) to create a case. All of them are deleted after the test.
    created = []

    def make(**fields):
        body = {"complaint": "Test complaint", "triage_level": "urgent", **fields}
        response = client.post("/emergency/", json=body)
        assert response.status_code == 201, response.text
        created.append(response.json()["id"])
        return response.json()

    yield make
    for case_id in created:
        client.delete(f"/emergency/{case_id}")


def test_register_known_patient(new_case, patient):
    case = new_case(patient_id=patient["id"])
    assert case["patient_name"] == patient["name"]
    assert case["status"] == "waiting"
    assert case["doctor_id"] is None
    assert case["wait_minutes"] == 0


def test_register_unknown_patient(new_case):
    case = new_case(patient_description="Unknown woman, around 50")
    assert case["patient_id"] is None
    assert case["patient_description"] == "Unknown woman, around 50"


def test_patient_or_description_required(client):
    response = client.post("/emergency/", json={"complaint": "Fall", "triage_level": "urgent"})
    assert response.status_code == 422


def test_invalid_triage_level_returns_422(client, patient):
    response = client.post("/emergency/", json={
        "patient_id": patient["id"], "complaint": "Fall", "triage_level": "very bad",
    })
    assert response.status_code == 422


def test_unknown_patient_id_returns_400(client):
    response = client.post("/emergency/", json={
        "patient_id": 999999, "complaint": "Fall", "triage_level": "urgent",
    })
    assert response.status_code == 400
    assert "Patient 999999" in response.json()["detail"]


def test_only_one_open_case_per_patient(client, new_case, patient):
    new_case(patient_id=patient["id"])
    response = client.post("/emergency/", json={
        "patient_id": patient["id"], "complaint": "Again", "triage_level": "urgent",
    })
    assert response.status_code == 409


def test_queue_puts_critical_first(client, new_case):
    mild = new_case(patient_description="Mild case", triage_level="non_urgent")
    severe = new_case(patient_description="Severe case", triage_level="critical")

    queue_ids = [c["id"] for c in client.get("/emergency/queue?limit=100").json()]
    assert queue_ids.index(severe["id"]) < queue_ids.index(mild["id"])


def test_patch_changes_triage_level(client, new_case):
    case = new_case(patient_description="Getting worse", triage_level="less_urgent")
    response = client.patch(f"/emergency/{case['id']}", json={"triage_level": "critical"})
    assert response.status_code == 200
    assert response.json()["triage_level"] == "critical"


def test_identify_unknown_patient(client, new_case, patient):
    case = new_case(patient_description="Unknown man")
    response = client.patch(f"/emergency/{case['id']}", json={"patient_id": patient["id"]})
    assert response.json()["patient_name"] == patient["name"]


def test_assign_requires_emergency_doctor(client, new_case, doctor):
    # The normal "doctor" fixture is in a test department, not Emergency Medicine.
    case = new_case(patient_description="Someone")
    response = client.patch(f"/emergency/{case['id']}/assign", json={"doctor_id": doctor["id"]})
    assert response.status_code == 400
    assert "Emergency Medicine" in response.json()["detail"]


def test_assign_unknown_doctor_returns_400(client, new_case):
    case = new_case(patient_description="Someone")
    response = client.patch(f"/emergency/{case['id']}/assign", json={"doctor_id": 999999})
    assert response.status_code == 400


def test_assign_starts_treatment_and_leaves_queue(client, new_case, emergency_doctor):
    case = new_case(patient_description="Someone")
    response = client.patch(f"/emergency/{case['id']}/assign", json={"doctor_id": emergency_doctor["id"]})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_treatment"
    assert data["doctor_name"] == emergency_doctor["name"]
    assert data["treated_at"] is not None

    queue_ids = [c["id"] for c in client.get("/emergency/queue?limit=100").json()]
    assert case["id"] not in queue_ids


def test_cannot_close_before_treatment(client, new_case):
    case = new_case(patient_description="Someone")
    response = client.patch(f"/emergency/{case['id']}/close", json={"outcome": "discharged"})
    assert response.status_code == 409
    assert "waiting" in response.json()["detail"]


def test_full_flow_and_closed_case_is_locked(client, new_case, emergency_doctor, patient):
    case = new_case(patient_id=patient["id"], triage_level="critical")
    client.patch(f"/emergency/{case['id']}/assign", json={"doctor_id": emergency_doctor["id"]})

    closed = client.patch(f"/emergency/{case['id']}/close", json={
        "outcome": "admitted", "notes": "Moved to cardiology ward",
    })
    assert closed.status_code == 200
    assert closed.json()["status"] == "admitted"
    assert closed.json()["closed_at"] is not None

    # A closed case can't be changed, reassigned or closed again.
    assert client.patch(f"/emergency/{case['id']}", json={"triage_level": "urgent"}).status_code == 409
    assert client.patch(
        f"/emergency/{case['id']}/assign", json={"doctor_id": emergency_doctor["id"]}
    ).status_code == 409
    assert client.patch(f"/emergency/{case['id']}/close", json={"outcome": "discharged"}).status_code == 409

    # Once closed, the same patient can come back with a new case.
    new_case(patient_id=patient["id"])


def test_filter_by_status(client, new_case, emergency_doctor):
    case = new_case(patient_description="Someone")
    client.patch(f"/emergency/{case['id']}/assign", json={"doctor_id": emergency_doctor["id"]})

    in_treatment = [c["id"] for c in client.get("/emergency/?status=in_treatment&limit=100").json()]
    waiting = [c["id"] for c in client.get("/emergency/?status=waiting&limit=100").json()]
    assert case["id"] in in_treatment
    assert case["id"] not in waiting


def test_missing_case_returns_404(client):
    assert client.get("/emergency/999999").status_code == 404
    assert client.patch("/emergency/999999/close", json={"outcome": "discharged"}).status_code == 404
    assert client.patch("/emergency/999999/assign", json={"doctor_id": 999999}).status_code == 404


def test_register_requires_login(client):
    response = client.post("/emergency/", headers=NO_AUTH, json={
        "patient_description": "Someone", "complaint": "Fall", "triage_level": "urgent",
    })
    assert response.status_code == 401


def test_staff_cannot_delete(client, new_case, staff_headers):
    case = new_case(patient_description="Someone")
    assert client.delete(f"/emergency/{case['id']}", headers=staff_headers).status_code == 403


def test_deleting_patient_deletes_their_cases(client, new_case, patient):
    case = new_case(patient_id=patient["id"])
    client.delete(f"/patients/{patient['id']}")
    assert client.get(f"/emergency/{case['id']}").status_code == 404
