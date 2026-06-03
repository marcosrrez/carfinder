import pytest
from unittest.mock import patch, MagicMock
from scanner.marketcheck import fetch_marketcheck_listings
from scanner.playwright_scraper import fetch_playwright_listings

FAKE_RESPONSE = {
    "listings": [
        {
            "id": "mc_001",
            "heading": "2016 Toyota Highlander XLE",
            "price": 17995,
            "miles": 89200,
            "dealer": {"city": "Fayetteville", "state": "AR"},
            "dist": 28.3,
            "vdp_url": "https://example.com/listing/mc_001",
        },
        {
            "id": "mc_002",
            "heading": "2016 Toyota Highlander LE",
            "price": 25000,
            "miles": 74500,
            "dealer": {"city": "Tulsa", "state": "OK"},
            "dist": 87.1,
            "vdp_url": "https://example.com/listing/mc_002",
        },
    ]
}

def test_fetch_returns_normalized_listings():
    mock_resp = MagicMock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("scanner.marketcheck.requests.get", return_value=mock_resp):
        results = fetch_marketcheck_listings()

    assert len(results) == 2
    assert results[0]["id"] == "mc_mc_001"
    assert results[0]["price"] == 17995
    assert results[0]["miles"] == 89200
    assert results[0]["city"] == "Fayetteville"
    assert results[0]["state"] == "AR"
    assert results[0]["distance"] == 28.3
    assert results[0]["source"] == "marketcheck"
    assert results[0]["url"] == "https://example.com/listing/mc_001"
    assert results[0]["title"] == "2016 Toyota Highlander XLE"

def test_playwright_returns_list_on_failure():
    # Scraper should never crash the scan — returns [] on any error
    with patch("scanner.playwright_scraper.sync_playwright") as mock_pw:
        mock_pw.side_effect = Exception("browser unavailable")
        result = fetch_playwright_listings()
    assert result == []
