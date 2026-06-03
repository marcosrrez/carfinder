import pytest
from unittest.mock import patch, MagicMock
from email_alert import build_email_body, send_alert

LISTINGS = [
    {"title": "2016 Toyota Highlander XLE", "price": 17995, "miles": 89200,
     "city": "Fayetteville", "state": "AR", "distance": 28.3,
     "source": "CarGurus", "url": "https://example.com/1", "score": "ideal"},
    {"title": "2016 Toyota Highlander LE", "price": 19500, "miles": 74500,
     "city": "Tulsa", "state": "OK", "distance": 87.1,
     "source": "AutoTrader", "url": "https://example.com/2", "score": "good"},
]

def test_build_email_body_contains_titles():
    body = build_email_body(LISTINGS)
    assert "2016 Toyota Highlander XLE" in body
    assert "2016 Toyota Highlander LE" in body

def test_build_email_body_groups_by_score():
    body = build_email_body(LISTINGS)
    ideal_pos = body.index("IDEAL")
    good_pos = body.index("GOOD")
    assert ideal_pos < good_pos

def test_build_email_body_contains_price():
    body = build_email_body(LISTINGS)
    assert "$17,995" in body

def test_send_alert_skips_when_empty():
    with patch("email_alert.smtplib.SMTP_SSL") as mock_smtp:
        send_alert([])
    mock_smtp.assert_not_called()

def test_send_alert_calls_smtp_with_listings():
    mock_server = MagicMock()
    with patch("email_alert.smtplib.SMTP_SSL") as mock_smtp:
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        send_alert(LISTINGS)
    mock_smtp.assert_called_once()
