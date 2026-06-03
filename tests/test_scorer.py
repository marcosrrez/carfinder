import pytest
from scorer import score_listing

def _listing(price, miles):
    return {"price": price, "miles": miles}

def test_ideal():
    assert score_listing(_listing(17000, 85000)) == "ideal"

def test_ideal_boundary():
    assert score_listing(_listing(18500, 90000)) == "ideal"

def test_good_price_over_ideal():
    assert score_listing(_listing(19000, 75000)) == "good"

def test_good_miles_over_ideal():
    assert score_listing(_listing(18000, 95000)) == "good"

def test_good_boundary():
    assert score_listing(_listing(20600, 80000)) == "good"

def test_ok():
    assert score_listing(_listing(16000, 120000)) == "ok"

def test_ok_boundary():
    assert score_listing(_listing(20600, 130000)) == "ok"

def test_no_match_price_too_high():
    assert score_listing(_listing(21000, 50000)) is None

def test_no_match_miles_too_high():
    assert score_listing(_listing(15000, 131000)) is None
