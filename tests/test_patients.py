def test_create_and_get_patient(client, patient):
    response = client.get(f"/patients/{patient['id']}")
    assert response.status_code == 200
    assert response.json()["date_of_birth"] == "1990-01-01"


def test_search_patient_by_name(client, patient):
    # Search with part of the name, in a different case
    part = patient["name"].split()[-1].upper()
    response = client.get(f"/patients/?name={part}")
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [patient["id"]]


def test_invalid_date_returns_422(client):
    response = client.post("/patients/", json={"name": "Bad Date", "date_of_birth": "01/01/1990"})
    assert response.status_code == 422


def test_patch_patient(client, patient):
    response = client.patch(f"/patients/{patient['id']}", json={"blood_group": "B+"})
    assert response.status_code == 200
    assert response.json()["blood_group"] == "B+"
    assert response.json()["name"] == patient["name"]


def test_delete_patient(client):
    created = client.post("/patients/", json={"name": "Temp Patient"}).json()
    assert client.delete(f"/patients/{created['id']}").status_code == 200
    assert client.get(f"/patients/{created['id']}").status_code == 404
