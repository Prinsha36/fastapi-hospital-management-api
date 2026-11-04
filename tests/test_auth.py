import uuid

from tests.conftest import ADMIN_USERNAME, NO_AUTH, STAFF_USERNAME, TEST_PASSWORD, unique


def login(client, username, password):
    return client.post("/auth/login", data={"username": username, "password": password}, headers=NO_AUTH)


def test_login_returns_token(client):
    response = login(client, ADMIN_USERNAME, TEST_PASSWORD)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password_returns_401(client):
    assert login(client, ADMIN_USERNAME, "wrong-password").status_code == 401


def test_login_unknown_user_returns_401(client):
    assert login(client, "nobody_here", "whatever").status_code == 401


def test_token_from_login_works(client):
    token = login(client, STAFF_USERNAME, TEST_PASSWORD).json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == STAFF_USERNAME
    assert "hashed_password" not in response.json()


def test_reading_data_needs_no_login(client):
    assert client.get("/departments/", headers=NO_AUTH).status_code == 200


def test_creating_without_login_returns_401(client):
    response = client.post("/departments/", json={"name": unique("X"), "description": "x"}, headers=NO_AUTH)
    assert response.status_code == 401


def test_fake_token_returns_401(client):
    response = client.post(
        "/patients/", json={"name": "X"}, headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_staff_can_create_but_not_delete(client, staff_headers):
    created = client.post("/patients/", json={"name": unique("Staff Patient")}, headers=staff_headers)
    assert created.status_code == 201
    patient_id = created.json()["id"]

    assert client.delete(f"/patients/{patient_id}", headers=staff_headers).status_code == 403
    assert client.delete(f"/patients/{patient_id}").status_code == 200  # admin can


def test_register_needs_admin(client, staff_headers):
    body = {"username": f"u_{uuid.uuid4().hex[:8]}", "password": "secret123"}
    assert client.post("/auth/register", json=body, headers=NO_AUTH).status_code == 401
    assert client.post("/auth/register", json=body, headers=staff_headers).status_code == 403


def test_admin_can_register_and_delete_user(client):
    body = {"username": f"u_{uuid.uuid4().hex[:8]}", "password": "secret123", "role": "staff"}
    created = client.post("/auth/register", json=body)
    assert created.status_code == 201
    assert created.json()["role"] == "staff"
    assert "password" not in created.json() and "hashed_password" not in created.json()

    assert client.post("/auth/register", json=body).status_code == 409  # same username
    assert login(client, body["username"], "secret123").status_code == 200
    assert client.delete(f"/auth/users/{created.json()['id']}").status_code == 200


def test_short_password_returns_422(client):
    body = {"username": f"u_{uuid.uuid4().hex[:8]}", "password": "123"}
    assert client.post("/auth/register", json=body).status_code == 422


def test_only_admin_can_list_users(client, staff_headers):
    assert client.get("/auth/users").status_code == 200
    assert client.get("/auth/users", headers=staff_headers).status_code == 403
