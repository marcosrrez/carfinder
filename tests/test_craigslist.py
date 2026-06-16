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


from unittest.mock import patch, MagicMock
from scanner.craigslist import fetch_craigslist_listings, _parse_miles_from_title


def test_parse_miles_from_title_k_notation():
    assert _parse_miles_from_title("2016 Toyota Highlander 89k miles") == 89000


def test_parse_miles_from_title_full():
    assert _parse_miles_from_title("2016 Highlander 102,000 miles") == 102000


def test_parse_miles_from_title_none():
    assert _parse_miles_from_title("2016 Toyota Highlander XLE") is None


def test_fetch_craigslist_returns_empty_on_playwright_error():
    with patch("scanner.craigslist.sync_playwright") as mock_pw:
        mock_pw.side_effect = Exception("browser not found")
        result = fetch_craigslist_listings({"id": "s1", "make": "Toyota",
            "model": "Highlander", "year": 2016, "max_price": 20000,
            "max_miles": 130000, "zip": "72761", "radius_miles": 100})
    assert result == []


def test_fetch_craigslist_returns_empty_on_bad_zip():
    result = fetch_craigslist_listings({"id": "s1", "make": "Toyota",
        "model": "Highlander", "year": 2016, "max_price": 20000,
        "max_miles": 130000, "zip": "00000", "radius_miles": 100})
    assert result == []
