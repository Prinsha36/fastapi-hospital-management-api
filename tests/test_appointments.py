import pytest
from tests.conftest import future_time


@pytest.fixture
def appointment(client, patient, doctor):
    response = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(),
        "reason": "Test visit",
    })
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/appointments/{data['id']}")


def test_create_appointment_shows_names(appointment, patient, doctor):
    assert appointment["patient_name"] == patient["name"]
    assert appointment["doctor_name"] == doctor["name"]
    assert appointment["status"] == "scheduled"


def test_double_booking_returns_409(client, appointment, patient, doctor):
    response = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(),
    })
    assert response.status_code == 409


def test_cancelling_frees_the_slot(client, appointment, patient, doctor):
    cancelled = client.patch(f"/appointments/{appointment['id']}", json={"status": "cancelled"})
    assert cancelled.json()["status"] == "cancelled"

    rebooked = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(),
    })
    assert rebooked.status_code == 201
    client.delete(f"/appointments/{rebooked.json()['id']}")


def test_past_time_returns_400(client, patient, doctor):
    response = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": "2020-01-01T10:00",
    })
    assert response.status_code == 400


def test_unknown_patient_returns_400(client, doctor):
    response = client.post("/appointments/", json={
        "patient_id": 999999,
        "doctor_id": doctor["id"],
        "appointment_time": future_time(),
    })
    assert response.status_code == 400
    assert "Patient 999999" in response.json()["detail"]


def test_invalid_status_returns_422(client, patient, doctor):
    response = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(),
        "status": "sunday",
    })
    assert response.status_code == 422


def test_filter_by_doctor(client, appointment, doctor):
    response = client.get(f"/appointments/?doctor_id={doctor['id']}")
    assert [a["id"] for a in response.json()] == [appointment["id"]]


def test_patient_and_doctor_shortcuts(client, appointment, patient, doctor):
    assert appointment["id"] in [a["id"] for a in client.get(f"/patients/{patient['id']}/appointments").json()]
    assert appointment["id"] in [a["id"] for a in client.get(f"/doctors/{doctor['id']}/appointments").json()]


def test_deleting_patient_deletes_their_appointments(client, patient, doctor):
    created = client.post("/appointments/", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_time": future_time(days=40),
    }).json()
    client.delete(f"/patients/{patient['id']}")
    assert client.get(f"/appointments/{created['id']}").status_code == 404
