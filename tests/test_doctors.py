import uuid


def test_create_doctor_in_department(client, doctor, department):
    assert doctor["department_id"] == department["id"]


def test_department_lists_its_doctors(client, doctor, department):
    response = client.get(f"/departments/{department['id']}/doctors")
    assert response.status_code == 200
    assert doctor["id"] in [d["id"] for d in response.json()]


def test_unknown_department_returns_400(client):
    response = client.post("/doctors/", json={
        "name": "Dr. Nobody",
        "specialization": "None",
        "department_id": 999999,
    })
    assert response.status_code == 400
    assert "999999" in response.json()["detail"]


def test_duplicate_email_returns_409(client, doctor):
    response = client.post("/doctors/", json={
        "name": "Dr. Copy",
        "specialization": "Copy",
        "email": doctor["email"],
    })
    assert response.status_code == 409


def test_doctor_without_department_is_allowed(client):
    response = client.post("/doctors/", json={
        "name": "Dr. Freelance",
        "specialization": "General",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
    })
    assert response.status_code == 201
    assert response.json()["department_id"] is None
    client.delete(f"/doctors/{response.json()['id']}")


def test_patch_doctor(client, doctor):
    response = client.patch(f"/doctors/{doctor['id']}", json={"phone": "9800099999"})
    assert response.status_code == 200
    assert response.json()["phone"] == "9800099999"
    assert response.json()["name"] == doctor["name"]


def test_deleting_department_keeps_doctor(client, doctor, department):
    client.delete(f"/departments/{department['id']}")
    response = client.get(f"/doctors/{doctor['id']}")
    assert response.status_code == 200
    assert response.json()["department_id"] is None


def test_missing_doctor_returns_404(client):
    assert client.get("/doctors/999999").status_code == 404
