# Checks that bad input is rejected with 422, and messy input is cleaned up.
import pytest


def error_fields(response):
    # e.g. ["phone", "email"]
    return [err["loc"][-1] for err in response.json()["detail"]]


@pytest.mark.parametrize("phone", ["abc", "123", "98000000011111111", "98-00-ab-0000"])
def test_bad_phone_rejected(client, phone):
    response = client.post("/patients/", json={"name": "Test Person", "phone": phone})
    assert response.status_code == 422
    assert "phone" in error_fields(response)


def test_phone_is_cleaned(client):
    response = client.post("/patients/", json={"name": "Test Person", "phone": "+977 980-000-0001"})
    assert response.status_code == 201
    assert response.json()["phone"] == "+9779800000001"
    client.delete(f"/patients/{response.json()['id']}")


@pytest.mark.parametrize("email", ["notanemail", "a@", "@hospital.com", "a b@x.com"])
def test_bad_email_rejected(client, email):
    response = client.post("/doctors/", json={"name": "Dr. Test", "specialization": "X", "email": email})
    assert response.status_code == 422
    assert "email" in error_fields(response)


@pytest.mark.parametrize("group", ["C+", "A", "AB", "O++"])
def test_bad_blood_group_rejected(client, group):
    response = client.post("/patients/", json={"name": "Test Person", "blood_group": group})
    assert response.status_code == 422


def test_gender_and_blood_group_are_normalized(client):
    response = client.post("/patients/", json={"name": "Test Person", "gender": "female", "blood_group": "ab+"})
    assert response.status_code == 201
    assert response.json()["gender"] == "Female"
    assert response.json()["blood_group"] == "AB+"
    client.delete(f"/patients/{response.json()['id']}")


def test_bad_gender_rejected(client):
    response = client.post("/patients/", json={"name": "Test Person", "gender": "unknown"})
    assert response.status_code == 422


@pytest.mark.parametrize("dob", ["2999-01-01", "1850-05-05"])
def test_bad_birth_date_rejected(client, dob):
    response = client.post("/patients/", json={"name": "Test Person", "date_of_birth": dob})
    assert response.status_code == 422


@pytest.mark.parametrize("name", ["", "   ", "A", "x" * 101])
def test_bad_name_rejected(client, name):
    response = client.post("/patients/", json={"name": name})
    assert response.status_code == 422


def test_name_spaces_are_trimmed(client):
    response = client.post("/patients/", json={"name": "   Test Person   "})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Person"
    client.delete(f"/patients/{response.json()['id']}")


def test_empty_department_name_rejected(client):
    response = client.post("/departments/", json={"name": "  ", "description": "x"})
    assert response.status_code == 422


@pytest.mark.parametrize("bad_id", [0, -5])
def test_non_positive_ids_rejected(client, bad_id):
    response = client.post("/appointments/", json={
        "patient_id": bad_id, "doctor_id": 1, "appointment_time": "2030-01-01T10:00",
    })
    assert response.status_code == 422


@pytest.mark.parametrize("username", ["ab", "has space", "bad!name"])
def test_bad_username_rejected(client, username):
    response = client.post("/auth/register", json={"username": username, "password": "secret123"})
    assert response.status_code == 422
