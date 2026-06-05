# tests/test_api_listings.py
import pytest
from app import create_app

@pytest.fixture
def client_with_search(tmp_path):
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        headers = {"X-User-Id": "user_test_1", "Content-Type": "application/json"}
        r = c.post("/api/searches", headers=headers, json={
            "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
            "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
            "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
            "alert_email": "test@test.com",
        })
        search_id = r.get_json()["id"]
        yield c, search_id, headers

def test_listings_empty(client_with_search):
    client, sid, headers = client_with_search
    resp = client.get(f"/api/searches/{sid}/listings", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_save_and_unsave(client_with_search):
    client, sid, headers = client_with_search
    resp = client.post("/api/listings/mc_abc/save", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["saved"] is True
    resp2 = client.delete("/api/listings/mc_abc/save", headers=headers)
    assert resp2.get_json()["saved"] is False

def test_hide_and_unhide(client_with_search):
    client, sid, headers = client_with_search
    resp = client.post("/api/listings/mc_abc/hide", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["hidden"] is True
    resp2 = client.delete("/api/listings/mc_abc/hide", headers=headers)
    assert resp2.get_json()["hidden"] is False
