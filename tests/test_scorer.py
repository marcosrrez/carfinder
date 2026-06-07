# tests/test_scorer.py
import pytest
from scorer import score_listing, deal_for

SEARCH = {
    "max_price": 20600, "ideal_price": 18500,
    "max_miles": 130000, "ideal_miles": 90000,
}

def _listing(price, miles, market=None):
    return {"price": price, "miles": miles, "market": market or price}

def test_ideal():
    assert score_listing(_listing(17000, 85000), SEARCH) == "ideal"

def test_ideal_boundary():
    assert score_listing(_listing(18500, 90000), SEARCH) == "ideal"

def test_good():
    assert score_listing(_listing(18900, 75000), SEARCH) == "good"

def test_ok_near_price_cap():
    # within max but > 92% of max_price → ok
    assert score_listing(_listing(19200, 60000), SEARCH) == "ok"

def test_ok_near_miles_cap():
    # within max but > 92% of max_miles → ok
    assert score_listing(_listing(17000, 120000), SEARCH) == "ok"

def test_ok_high_miles():
    assert score_listing(_listing(18000, 95000), SEARCH) == "ok"

def test_ok_boundary():
    assert score_listing(_listing(20600, 130000), SEARCH) == "ok"

def test_none_price_too_high():
    assert score_listing(_listing(21000, 50000), SEARCH) is None

def test_none_miles_too_high():
    assert score_listing(_listing(15000, 131000), SEARCH) is None

def test_deal_great():
    d = deal_for(_listing(15000, 80000, market=17000))
    assert d["key"] == "great"
    assert d["delta"] == -2000

def test_deal_good():
    d = deal_for(_listing(16800, 80000, market=17500))
    assert d["key"] == "good"

def test_deal_fair():
    d = deal_for(_listing(17800, 80000, market=18000))
    assert d["key"] == "fair"

def test_deal_high():
    d = deal_for(_listing(20000, 80000, market=18000))
    assert d["key"] == "high"

from scorer import trim_matches

def test_trim_matches_when_listing_trim_in_selected():
    listing = {"trim": "XLE Premium", "title": "2016 Toyota Highlander XLE Premium"}
    search = {"trims": "XLE,Limited"}
    assert trim_matches(listing, search) is True

def test_trim_matches_uses_title_as_fallback():
    listing = {"trim": "", "title": "2016 Toyota Highlander XLE AWD"}
    search = {"trims": "XLE"}
    assert trim_matches(listing, search) is True

def test_trim_no_match():
    listing = {"trim": "LE", "title": "2016 Toyota Highlander LE"}
    search = {"trims": "XLE,Limited"}
    assert trim_matches(listing, search) is False

def test_trim_empty_trims_returns_false():
    listing = {"trim": "XLE", "title": ""}
    search = {"trims": ""}
    assert trim_matches(listing, search) is False

def test_trim_no_trims_key_returns_false():
    listing = {"trim": "XLE", "title": ""}
    search = {}
    assert trim_matches(listing, search) is False
