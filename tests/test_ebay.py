# tests/test_ebay.py
import pytest
from unittest.mock import patch, MagicMock
from scanner.ebay import fetch_ebay_listings, _normalize, clear_cache

SEARCH = {
    "id": "s1", "make": "Toyota", "model": "Highlander", "year": 2016,
    "max_price": 20600, "max_miles": 130000,
    "zip": "72761", "radius_miles": 100,
}

FAKE_ITEM = {
    "itemId": ["987654321"],
    "title": ["2016 Toyota Highlander XLE 4WD 89k miles"],
    "sellingStatus": [{"currentPrice": [{"__value__": "17995", "@currencyId": "USD"}]}],
    "listingInfo": [{"viewItemURL": ["https://www.ebay.com/itm/987654321"]}],
    "location": ["Tulsa, OK"],
    "pictureURLSuperSize": ["https://img.ebay.com/1.jpg", "https://img.ebay.com/2.jpg"],
}

FAKE_RESPONSE = {
    "findItemsAdvancedResponse": [{
        "ack": ["Success"],
        "searchResult": [{"@count": "1", "item": [FAKE_ITEM]}],
    }]
}


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


def test_normalize_extracts_fields():
    result = _normalize(FAKE_ITEM, "s1")
    assert result["id"] == "eb_987654321"
    assert result["search_id"] == "s1"
    assert result["price"] == 17995
    assert result["title"] == "2016 Toyota Highlander XLE 4WD 89k miles"
    assert result["city"] == "Tulsa"
    assert result["state"] == "OK"
    assert result["source"] == "ebay"
    assert result["photos"] == 2
    assert result["miles"] == 89000  # parsed from title


def test_normalize_miles_fallback_zero():
    item = dict(FAKE_ITEM)
    item["title"] = ["2016 Toyota Highlander XLE"]  # no miles in title
    result = _normalize(item, "s1")
    assert result["miles"] == 0


def test_fetch_returns_normalized_listings():
    mock_resp = MagicMock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("scanner.ebay.requests.get", return_value=mock_resp):
        results = fetch_ebay_listings(SEARCH)

    assert len(results) == 1
    assert results[0]["id"] == "eb_987654321"
    assert results[0]["price"] == 17995


def test_fetch_returns_empty_on_api_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("500")

    with patch("scanner.ebay.requests.get", return_value=mock_resp):
        results = fetch_ebay_listings(SEARCH)

    assert results == []


def test_fetch_uses_cache_on_second_call():
    mock_resp = MagicMock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("scanner.ebay.requests.get", return_value=mock_resp) as mock_get:
        fetch_ebay_listings(SEARCH)
        fetch_ebay_listings(SEARCH)
        assert mock_get.call_count == 1  # second call served from cache


def test_fetch_returns_empty_without_app_id():
    with patch("scanner.ebay.EBAY_APP_ID", None):
        results = fetch_ebay_listings(SEARCH)
    assert results == []
