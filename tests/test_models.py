# tests/test_models.py
import pytest
import tempfile
import os
from models import Database

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = Database(path)
    yield d
    d.close()
    os.unlink(path)

def test_create_search(db):
    s = db.create_search({
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_emails": "test@example.com", "user_id": "user_1",
    })
    assert s["id"] is not None
    assert s["make"] == "Toyota"

def test_get_search(db):
    s = db.create_search({
        "make": "Honda", "model": "Odyssey", "trim": "Elite", "year": 2020,
        "max_price": 34000, "ideal_price": 30000,
        "max_miles": 60000, "ideal_miles": 35000,
        "zip": "78745", "city": "Austin, TX",
        "radius_miles": 100, "interval_hours": 2,
        "alert_emails": "test@example.com", "user_id": "user_1",
    })
    fetched = db.get_search(s["id"])
    assert fetched["model"] == "Odyssey"

def test_list_searches_by_user(db):
    db.create_search({"make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_emails": "a@b.com", "user_id": "user_1"})
    db.create_search({"make": "Honda", "model": "Odyssey", "trim": "", "year": 2020,
        "max_price": 34000, "ideal_price": 30000, "max_miles": 60000, "ideal_miles": 35000,
        "zip": "78745", "city": "Austin, TX", "radius_miles": 100, "interval_hours": 2,
        "alert_emails": "a@b.com", "user_id": "user_2"})
    user1 = db.list_searches("user_1")
    assert len(user1) == 1
    assert user1[0]["make"] == "Toyota"

def test_upsert_listing(db):
    s = db.create_search({"make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_emails": "a@b.com", "user_id": "user_1"})
    listing = {
        "id": "mc_abc123", "search_id": s["id"],
        "title": "2016 Toyota Highlander XLE", "price": 17995, "miles": 89200,
        "city": "Fayetteville", "state": "AR", "distance": 28.3,
        "source": "marketcheck", "url": "https://example.com/1",
        "market": 18500, "drivetrain": "FWD", "exterior": "Blizzard Pearl",
        "interior": "Black leather", "owners": 1, "accidents": 0,
        "days_listed": 6, "photos": 24, "seller_type": "Dealer",
        "seller_name": "Round Rock Toyota", "seller_rating": 4.6,
        "vin": "5TDYK3DC4GS7****1", "drop_amount": None, "drop_when": None, "is_new": 1,
    }
    db.upsert_listing(listing)
    listings = db.get_listings(s["id"])
    assert len(listings) == 1
    assert listings[0]["price"] == 17995

def test_save_and_unsave_listing(db):
    db.save_listing("user_1", "mc_abc123")
    assert db.is_saved("user_1", "mc_abc123") is True
    db.unsave_listing("user_1", "mc_abc123")
    assert db.is_saved("user_1", "mc_abc123") is False

def test_hide_listing(db):
    db.hide_listing("user_1", "mc_xyz")
    assert db.is_hidden("user_1", "mc_xyz") is True

def test_get_saved_ids(db):
    db.save_listing("user_1", "mc_a")
    db.save_listing("user_1", "mc_b")
    db.save_listing("user_2", "mc_c")
    ids = db.get_saved_ids("user_1")
    assert set(ids) == {"mc_a", "mc_b"}
