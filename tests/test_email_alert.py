# tests/test_email_alert.py
import pytest
from unittest.mock import patch, MagicMock
from email_alert import build_email_body, send_alert

SEARCH = {
    "make": "Toyota", "model": "Highlander", "year": 2016,
    "max_price": 20600, "ideal_price": 18500,
    "max_miles": 130000, "ideal_miles": 90000,
    "alert_email": "test@example.com",
}

LISTINGS = [
    {"title": "2016 Toyota Highlander XLE", "price": 17995, "miles": 89200,
     "city": "Fayetteville", "state": "AR", "distance": 28.3,
     "source": "marketcheck", "url": "https://example.com/1",
     "tier": "ideal", "deal": {"key": "great", "label": "Great deal", "delta": -1400},
     "market": 19395},
    {"title": "2016 Toyota Highlander LE", "price": 19500, "miles": 74500,
     "city": "Tulsa", "state": "OK", "distance": 87.1,
     "source": "marketcheck", "url": "https://example.com/2",
     "tier": "good", "deal": {"key": "fair", "label": "Fair price", "delta": 200},
     "market": 19300},
]

def test_build_email_body_contains_titles():
    body = build_email_body(SEARCH, LISTINGS)
    assert "2016 Toyota Highlander XLE" in body
    assert "2016 Toyota Highlander LE" in body

def test_build_email_body_groups_by_tier():
    body = build_email_body(SEARCH, LISTINGS)
    assert body.index("IDEAL") < body.index("GOOD")

def test_build_email_body_contains_price():
    body = build_email_body(SEARCH, LISTINGS)
    assert "$17,995" in body

def test_build_email_body_contains_deal_signal():
    body = build_email_body(SEARCH, LISTINGS)
    assert "Great deal" in body

def test_send_alert_skips_empty():
    with patch("email_alert.resend.Emails.send") as mock_send:
        send_alert(SEARCH, [])
    mock_send.assert_not_called()

def test_send_alert_calls_resend():
    with patch("email_alert.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "abc"}
        send_alert(SEARCH, LISTINGS)
    mock_send.assert_called_once()
