from tests.conftest import unique


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["Database"] == "Connected"


def test_create_and_get_department(client, department):
    response = client.get(f"/departments/{department['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == department["name"]


def test_duplicate_department_name_returns_409(client, department):
    response = client.post("/departments/", json={
        "name": department["name"],
        "description": "Same name again",
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_patch_changes_only_sent_fields(client, department):
    response = client.patch(f"/departments/{department['id']}", json={"description": "New text"})
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New text"
    assert data["name"] == department["name"]  # unchanged


def test_put_replaces_department(client, department):
    new_name = unique("Renamed Dept")
    response = client.put(f"/departments/{department['id']}", json={
        "name": new_name,
        "description": "Replaced",
    })
    assert response.status_code == 200
    assert response.json()["name"] == new_name


def test_delete_department(client):
    created = client.post("/departments/", json={
        "name": unique("To Delete"), "description": "x",
    }).json()
    assert client.delete(f"/departments/{created['id']}").status_code == 200
    assert client.get(f"/departments/{created['id']}").status_code == 404


def test_missing_department_returns_404(client):
    assert client.get("/departments/999999").status_code == 404
    assert client.delete("/departments/999999").status_code == 404


def test_missing_name_returns_422(client):
    response = client.post("/departments/", json={"description": "No name"})
    assert response.status_code == 422


def test_pagination_limit(client):
    response = client.get("/departments/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2


def test_pagination_offset_moves_to_next_page(client):
    first = client.get("/departments/?limit=2&offset=0").json()
    second = client.get("/departments/?limit=2&offset=2").json()
    first_ids = {d["id"] for d in first}
    second_ids = {d["id"] for d in second}
    assert first_ids.isdisjoint(second_ids)


def test_bad_pagination_values_return_422(client):
    assert client.get("/departments/?limit=0").status_code == 422
    assert client.get("/departments/?limit=101").status_code == 422
    assert client.get("/departments/?offset=-1").status_code == 422
