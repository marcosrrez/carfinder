# tests/test_scanner.py
import pytest
from unittest.mock import patch, MagicMock
from scanner.marketcheck import fetch_marketcheck_listings, clear_cache
from scanner.playwright_scraper import fetch_playwright_listings
from scanner import run_scan, compute_market_values

@pytest.fixture(autouse=True)
def reset_marketcheck_cache():
    """Clear the Marketcheck query cache before each test to prevent pollution."""
    clear_cache()
    yield
    clear_cache()

SEARCH = {
    "id": "s1", "make": "Toyota", "model": "Highlander", "year": 2016,
    "max_price": 20600, "ideal_price": 18500,
    "max_miles": 130000, "ideal_miles": 90000,
    "zip": "72761", "radius_miles": 300,
}

FAKE_RESPONSE = {
    "listings": [
        {
            "id": "abc123", "heading": "2016 Toyota Highlander XLE",
            "price": 17995, "miles": 89200,
            "dealer": {"city": "Fayetteville", "state": "AR"},
            "dist": 28.3, "vdp_url": "https://example.com/1",
            "build": {"drivetrain": "FWD", "ext_color_generic": "Blizzard Pearl", "int_color_generic": "Black"},
            "extra": {"owner_count": 1, "accident_cnt": 0},
            "dom": 6, "media": {"photo_links": ["a","b"]},
            "seller": {"type": "D", "seller_name": "Round Rock Toyota", "dealer_rating": 4.6},
            "vin": "5TDYK****1", "price_history": None,
        }
    ]
}

def test_fetch_returns_normalized_listing():
    mock_resp = MagicMock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("scanner.marketcheck.requests.get", return_value=mock_resp):
        results = fetch_marketcheck_listings(SEARCH)

    assert len(results) == 1
    r = results[0]
    assert r["id"] == "mc_abc123"
    assert r["search_id"] == "s1"
    assert r["price"] == 17995
    assert r["miles"] == 89200
    assert r["drivetrain"] == "FWD"
    assert r["exterior"] == "Blizzard Pearl"
    assert r["owners"] == 1
    assert r["accidents"] == 0
    assert r["days_listed"] == 6
    assert r["photos"] == 2
    assert r["seller_type"] == "Dealer"
    assert r["seller_rating"] == 4.6

def test_compute_market_values_uses_median():
    listings = [
        {"id": "a", "price": 16000},
        {"id": "b", "price": 18000},
        {"id": "c", "price": 20000},
    ]
    result = compute_market_values(listings)
    assert result[0]["market"] == 18000
    assert result[1]["market"] == 18000
    assert result[2]["market"] == 18000

def test_playwright_returns_list_on_failure():
    with patch("scanner.craigslist.sync_playwright") as mock_pw:
        mock_pw.side_effect = Exception("browser unavailable")
        result = fetch_playwright_listings(SEARCH)
    assert result == []

def test_fetch_zip_passes_trim_and_drivetrain_when_set():
    """Scanner passes trim list and drivetrain to Marketcheck when set."""
    search = {
        "id": "s1", "year": 2016, "make": "Toyota", "model": "Highlander",
        "max_price": 25000, "max_miles": 130000,
        "trims": "XLE,Limited", "drivetrain": "AWD",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"listings": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("scanner.marketcheck.requests.get", return_value=mock_resp) as mock_get:
        from scanner.marketcheck import _fetch_raw as _fetch_zip
        _fetch_zip(search, "72761")
        call_params = mock_get.call_args[1]["params"]
        assert call_params.get("trim") == "XLE,Limited"
        assert call_params.get("drivetrain") == "AWD"

def test_fetch_zip_omits_trim_and_drivetrain_when_empty():
    """Scanner does not send trim or drivetrain when they are empty/Any."""
    search = {
        "id": "s1", "year": 2016, "make": "Toyota", "model": "Highlander",
        "max_price": 25000, "max_miles": 130000,
        "trims": "", "drivetrain": "Any",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"listings": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("scanner.marketcheck.requests.get", return_value=mock_resp) as mock_get:
        from scanner.marketcheck import _fetch_raw as _fetch_zip
        _fetch_zip(search, "72761")
        call_params = mock_get.call_args[1]["params"]
        assert "trim" not in call_params
        assert "drivetrain" not in call_params


def test_run_scan_deduplicates_by_id():
    """If two sources return same listing ID, only one appears in output."""
    dup_listing = {
        "id": "mc_shared123", "search_id": "s1",
        "title": "2016 Toyota Highlander XLE", "price": 17000, "miles": 80000,
        "city": "Tulsa", "state": "OK", "distance": 28,
        "source": "marketcheck", "url": "https://example.com/1",
        "market": None, "drivetrain": "", "exterior": "", "interior": "",
        "owners": None, "accidents": None, "days_listed": None, "photos": 2,
        "seller_type": "Dealer", "seller_name": "Test Dealer",
        "seller_rating": None, "vin": "", "drop_amount": None,
        "drop_when": None, "is_new": 1,
    }

    with patch("scanner.fetch_marketcheck_listings", return_value=[dup_listing]), \
         patch("scanner.fetch_ebay_listings", return_value=[{**dup_listing, "source": "ebay"}]), \
         patch("scanner.fetch_craigslist_listings", return_value=[]):
        results = run_scan(SEARCH)

    ids = [r["id"] for r in results]
    assert ids.count("mc_shared123") == 1


def test_run_scan_merges_all_sources():
    """run_scan combines marketcheck, ebay, and craigslist listings."""
    mc = {"id": "mc_1", "search_id": "s1", "title": "2016 Toyota Highlander XLE",
          "price": 17000, "miles": 80000, "city": "A", "state": "AR", "distance": 10,
          "source": "marketcheck", "url": "https://mc.com/1", "market": None,
          "drivetrain": "", "exterior": "", "interior": "", "owners": None,
          "accidents": None, "days_listed": None, "photos": 0, "seller_type": "Dealer",
          "seller_name": "", "seller_rating": None, "vin": "", "drop_amount": None,
          "drop_when": None, "is_new": 1}
    eb = {**mc, "id": "eb_1", "source": "ebay", "price": 16000}
    cl = {**mc, "id": "cl_1", "source": "craigslist", "price": 15500}

    with patch("scanner.fetch_marketcheck_listings", return_value=[mc]), \
         patch("scanner.fetch_ebay_listings", return_value=[eb]), \
         patch("scanner.fetch_craigslist_listings", return_value=[cl]):
        results = run_scan(SEARCH)

    sources = {r["source"] for r in results}
    assert "marketcheck" in sources
    assert "ebay" in sources
    assert "craigslist" in sources
