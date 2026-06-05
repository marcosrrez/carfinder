# tests/test_api_searches.py
import pytest
import json
from app import create_app

@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

HEADERS = {"X-User-Id": "user_test_1", "Content-Type": "application/json"}

def test_create_search(client):
    resp = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["make"] == "Toyota"
    assert data["id"] is not None

def test_list_searches_empty(client):
    resp = client.get("/api/searches", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_list_searches(client):
    client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    resp = client.get("/api/searches", headers=HEADERS)
    assert len(resp.get_json()) == 1

def test_update_search(client):
    create = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    sid = create.get_json()["id"]
    resp = client.put(f"/api/searches/{sid}", headers=HEADERS, json={"max_price": 22000})
    assert resp.status_code == 200
    assert resp.get_json()["max_price"] == 22000

def test_delete_search(client):
    create = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    sid = create.get_json()["id"]
    resp = client.delete(f"/api/searches/{sid}", headers=HEADERS)
    assert resp.status_code == 200
    assert client.get("/api/searches", headers=HEADERS).get_json() == []

def test_requires_user_header(client):
    resp = client.get("/api/searches")
    assert resp.status_code == 401
