# tests/test_email_alert.py
import pytest
from unittest.mock import patch, MagicMock
from email_alert import build_email_html, build_email_text, send_alert

SEARCH = {
    "make": "Toyota", "model": "Highlander", "year": 2016,
    "max_price": 20600, "ideal_price": 18500,
    "max_miles": 130000, "ideal_miles": 90000,
    "alert_emails": "test@example.com",
}

LISTINGS = [
    {"title": "2016 Toyota Highlander XLE", "price": 17995, "miles": 89200,
     "city": "Fayetteville", "state": "AR", "distance": 28.3,
     "source": "marketcheck", "url": "https://example.com/1",
     "tier": "ideal", "drivetrain": "AWD", "exterior": "Silver",
     "days_listed": 3, "seller_type": "Dealer",
     "drop_amount": 1400, "drop_when": "2 days ago"},
    {"title": "2016 Toyota Highlander LE", "price": 19500, "miles": 74500,
     "city": "Tulsa", "state": "OK", "distance": 87.1,
     "source": "marketcheck", "url": "https://example.com/2",
     "tier": "good", "drivetrain": "FWD", "exterior": "White",
     "days_listed": 12, "seller_type": "Dealer",
     "drop_amount": None, "drop_when": None},
]

def test_build_email_html_contains_titles():
    html = build_email_html(SEARCH, LISTINGS)
    assert "2016 Toyota Highlander XLE" in html
    assert "2016 Toyota Highlander LE" in html

def test_build_email_html_groups_by_tier():
    html = build_email_html(SEARCH, LISTINGS)
    assert html.index("Ideal") < html.index("Good")

def test_build_email_html_contains_price():
    html = build_email_html(SEARCH, LISTINGS)
    assert "$17,995" in html

def test_build_email_html_contains_price_drop():
    html = build_email_html(SEARCH, LISTINGS)
    assert "Price dropped" in html
    assert "$1,400" in html

def test_build_email_text_contains_titles():
    text = build_email_text(SEARCH, LISTINGS)
    assert "2016 Toyota Highlander XLE" in text
    assert "2016 Toyota Highlander LE" in text

def test_send_alert_skips_empty():
    with patch("email_alert.resend.Emails.send") as mock_send:
        send_alert(SEARCH, [])
    mock_send.assert_not_called()

def test_send_alert_calls_resend():
    with patch("email_alert.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "abc"}
        send_alert(SEARCH, LISTINGS)
    mock_send.assert_called_once()
