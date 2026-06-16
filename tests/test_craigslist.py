# tests/test_craigslist.py
import pytest
from scanner.markets import craigslist_markets_near, zip_to_coords


def test_zip_to_coords_known_zip():
    lat, lon = zip_to_coords("10001")  # Manhattan
    assert 40.0 < lat < 41.0
    assert -75.0 < lon < -73.0


def test_zip_to_coords_unknown_returns_none():
    result = zip_to_coords("00000")
    assert result is None


def test_markets_near_tulsa():
    """72761 is in NW Arkansas — Tulsa and Fayetteville should be within 100 miles."""
    markets = craigslist_markets_near("72761", 100)
    subdomains = [m[1] for m in markets]
    assert "tulsa" in subdomains
    assert "fayar" in subdomains


def test_markets_near_nyc_excludes_far():
    """NYC ZIP — Tulsa should NOT be within 200 miles."""
    markets = craigslist_markets_near("10001", 200)
    subdomains = [m[1] for m in markets]
    assert "tulsa" not in subdomains


def test_markets_returns_list_of_tuples():
    markets = craigslist_markets_near("90210", 150)
    assert isinstance(markets, list)
    for m in markets:
        assert len(m) == 2
        assert isinstance(m[0], str)
        assert isinstance(m[1], str)


def test_markets_empty_for_bad_zip():
    result = craigslist_markets_near("00000", 100)
    assert result == []
