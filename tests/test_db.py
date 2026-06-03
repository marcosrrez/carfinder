import pytest
import tempfile
import os
from db import ListingDB


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = ListingDB(path)
    yield d
    os.unlink(path)


def test_new_listing_not_seen(db):
    assert db.is_new("abc123") is True


def test_seen_listing_after_mark(db):
    db.mark_seen("abc123")
    assert db.is_new("abc123") is False


def test_filter_new_keeps_unseen(db):
    listings = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    db.mark_seen("b")
    result = db.filter_new(listings)
    assert [l["id"] for l in result] == ["a", "c"]


def test_filter_new_marks_as_seen(db):
    listings = [{"id": "x"}]
    db.filter_new(listings)
    assert db.is_new("x") is False
