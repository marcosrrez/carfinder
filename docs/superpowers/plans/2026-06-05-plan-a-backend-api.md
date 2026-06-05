# CarFinder Plan A — Backend API Refactor

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Flask app from a single-search Jinja template server into a full multi-search REST JSON API that supports multiple searches, rich listing data, save/hide per user, deal scoring, and market value estimation.

**Architecture:** SQLite database with proper relational schema (searches, listings, saved, hidden, users tables). Flask serves a pure JSON API with CORS enabled for the React frontend. The scanner is refactored to support multiple search profiles and enrich each listing with market value (computed as the median price of all results in that scan). The scheduler loops over all active searches every N hours.

**Tech Stack:** Python 3.11+, Flask 3, Flask-CORS, SQLite (stdlib), APScheduler, Requests, Playwright, Resend, pytest

---

## File Structure

```
carfinder/
├── api/
│   ├── __init__.py          # Blueprint registration
│   ├── searches.py          # GET/POST/PUT/DELETE /api/searches
│   ├── listings.py          # GET /api/searches/:id/listings, save/hide endpoints
│   └── scan.py              # POST /api/scan (global), POST /api/searches/:id/scan
├── scanner/
│   ├── __init__.py          # run_scan(search: dict) → list[dict]  (MODIFIED)
│   ├── marketcheck.py       # fetch_marketcheck_listings(search) → enriched list (MODIFIED)
│   └── playwright_scraper.py # fetch_playwright_listings(search) → list (MODIFIED)
├── models.py                # DB schema creation, helper queries
├── scorer.py                # score_listing(listing, search) → tier str (MODIFIED - uses idealPrice)
├── email_alert.py           # send_alert(search, new_listings) — multi-search (MODIFIED)
├── scheduler.py             # loops all active searches (MODIFIED)
├── app.py                   # Flask app factory, CORS, blueprint registration (REWRITTEN)
├── config.py                # env loading (unchanged)
├── db.py                    # ListingDB dedup store (unchanged)
└── tests/
    ├── test_scorer.py        # UPDATE for new signature
    ├── test_models.py        # NEW
    ├── test_api_searches.py  # NEW
    └── test_api_listings.py  # NEW
```

---

## Task 1: Install Flask-CORS

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add flask-cors to requirements.txt**

```
flask==3.0.3
flask-cors==4.0.1
apscheduler==3.10.4
playwright==1.44.0
requests==2.32.3
python-dotenv==1.0.1
pytest==8.2.0
resend==2.30.1
```

- [ ] **Step 2: Install**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && pip install flask-cors==4.0.1
```

Expected: `Successfully installed flask-cors-4.0.1`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add flask-cors dependency"
```

---

## Task 2: New Database Schema

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
import pytest
import tempfile
import os
from models import Database

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = Database(path)
    yield d
    d.close()
    os.unlink(path)

def test_create_search(db):
    s = db.create_search({
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@example.com", "user_id": "user_1",
    })
    assert s["id"] is not None
    assert s["make"] == "Toyota"

def test_get_search(db):
    s = db.create_search({
        "make": "Honda", "model": "Odyssey", "trim": "Elite", "year": 2020,
        "max_price": 34000, "ideal_price": 30000,
        "max_miles": 60000, "ideal_miles": 35000,
        "zip": "78745", "city": "Austin, TX",
        "radius_miles": 100, "interval_hours": 2,
        "alert_email": "test@example.com", "user_id": "user_1",
    })
    fetched = db.get_search(s["id"])
    assert fetched["model"] == "Odyssey"

def test_list_searches_by_user(db):
    db.create_search({"make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "a@b.com", "user_id": "user_1"})
    db.create_search({"make": "Honda", "model": "Odyssey", "trim": "", "year": 2020,
        "max_price": 34000, "ideal_price": 30000, "max_miles": 60000, "ideal_miles": 35000,
        "zip": "78745", "city": "Austin, TX", "radius_miles": 100, "interval_hours": 2,
        "alert_email": "a@b.com", "user_id": "user_2"})
    user1 = db.list_searches("user_1")
    assert len(user1) == 1
    assert user1[0]["make"] == "Toyota"

def test_upsert_listing(db):
    s = db.create_search({"make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "a@b.com", "user_id": "user_1"})
    listing = {
        "id": "mc_abc123", "search_id": s["id"],
        "title": "2016 Toyota Highlander XLE", "price": 17995, "miles": 89200,
        "city": "Fayetteville", "state": "AR", "distance": 28.3,
        "source": "marketcheck", "url": "https://example.com/1",
        "market": 18500, "drivetrain": "FWD", "exterior": "Blizzard Pearl",
        "interior": "Black leather", "owners": 1, "accidents": 0,
        "days_listed": 6, "photos": 24, "seller_type": "Dealer",
        "seller_name": "Round Rock Toyota", "seller_rating": 4.6,
        "vin": "5TDYK3DC4GS7****1", "drop_amount": None, "drop_when": None, "is_new": 1,
    }
    db.upsert_listing(listing)
    listings = db.get_listings(s["id"])
    assert len(listings) == 1
    assert listings[0]["price"] == 17995

def test_save_and_unsave_listing(db):
    db.save_listing("user_1", "mc_abc123")
    assert db.is_saved("user_1", "mc_abc123") is True
    db.unsave_listing("user_1", "mc_abc123")
    assert db.is_saved("user_1", "mc_abc123") is False

def test_hide_listing(db):
    db.hide_listing("user_1", "mc_xyz")
    assert db.is_hidden("user_1", "mc_xyz") is True

def test_get_saved_ids(db):
    db.save_listing("user_1", "mc_a")
    db.save_listing("user_1", "mc_b")
    db.save_listing("user_2", "mc_c")
    ids = db.get_saved_ids("user_1")
    assert set(ids) == {"mc_a", "mc_b"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && pytest tests/test_models.py -v
```

Expected: `ImportError: No module named 'models'`

- [ ] **Step 3: Implement models.py**

```python
# models.py
import sqlite3
import uuid
from datetime import datetime

class Database:
    def __init__(self, path: str = "carfinder.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS searches (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                trim TEXT DEFAULT '',
                year INTEGER NOT NULL,
                max_price INTEGER NOT NULL,
                ideal_price INTEGER NOT NULL,
                max_miles INTEGER NOT NULL,
                ideal_miles INTEGER NOT NULL,
                zip TEXT NOT NULL,
                city TEXT NOT NULL,
                radius_miles INTEGER NOT NULL DEFAULT 300,
                interval_hours INTEGER NOT NULL DEFAULT 2,
                alert_email TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS listings (
                id TEXT NOT NULL,
                search_id TEXT NOT NULL,
                title TEXT,
                price INTEGER,
                miles INTEGER,
                city TEXT,
                state TEXT,
                distance REAL,
                source TEXT,
                url TEXT,
                market INTEGER,
                drivetrain TEXT,
                exterior TEXT,
                interior TEXT,
                owners INTEGER,
                accidents INTEGER,
                days_listed INTEGER,
                photos INTEGER,
                seller_type TEXT,
                seller_name TEXT,
                seller_rating REAL,
                vin TEXT,
                drop_amount INTEGER,
                drop_when TEXT,
                is_new INTEGER DEFAULT 1,
                first_seen TEXT,
                last_seen TEXT,
                PRIMARY KEY (id, search_id),
                FOREIGN KEY (search_id) REFERENCES searches(id)
            );

            CREATE TABLE IF NOT EXISTS saved_listings (
                user_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                PRIMARY KEY (user_id, listing_id)
            );

            CREATE TABLE IF NOT EXISTS hidden_listings (
                user_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                hidden_at TEXT NOT NULL,
                PRIMARY KEY (user_id, listing_id)
            );
        """)
        self.conn.commit()

    def _row_to_dict(self, row) -> dict:
        return dict(row) if row else None

    # ── Searches ──────────────────────────────────────────────────────────

    def create_search(self, data: dict) -> dict:
        search_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO searches
            (id, user_id, make, model, trim, year, max_price, ideal_price,
             max_miles, ideal_miles, zip, city, radius_miles, interval_hours,
             alert_email, active, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)
        """, (search_id, data["user_id"], data["make"], data["model"],
              data.get("trim", ""), data["year"], data["max_price"],
              data["ideal_price"], data["max_miles"], data["ideal_miles"],
              data["zip"], data["city"], data["radius_miles"],
              data["interval_hours"], data["alert_email"], now))
        self.conn.commit()
        return self.get_search(search_id)

    def get_search(self, search_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM searches WHERE id = ?", (search_id,)
        ).fetchone()
        return self._row_to_dict(row)

    def list_searches(self, user_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM searches WHERE user_id = ? AND active = 1 ORDER BY created_at",
            (user_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def list_all_active_searches(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM searches WHERE active = 1"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_search(self, search_id: str, data: dict) -> dict:
        fields = ["make", "model", "trim", "year", "max_price", "ideal_price",
                  "max_miles", "ideal_miles", "zip", "city", "radius_miles",
                  "interval_hours", "alert_email"]
        sets = ", ".join(f"{f} = ?" for f in fields if f in data)
        vals = [data[f] for f in fields if f in data] + [search_id]
        if sets:
            self.conn.execute(f"UPDATE searches SET {sets} WHERE id = ?", vals)
            self.conn.commit()
        return self.get_search(search_id)

    def delete_search(self, search_id: str) -> None:
        self.conn.execute(
            "UPDATE searches SET active = 0 WHERE id = ?", (search_id,)
        )
        self.conn.commit()

    # ── Listings ──────────────────────────────────────────────────────────

    def upsert_listing(self, listing: dict) -> None:
        now = datetime.now().isoformat()
        existing = self.conn.execute(
            "SELECT id FROM listings WHERE id = ? AND search_id = ?",
            (listing["id"], listing["search_id"])
        ).fetchone()
        if existing:
            self.conn.execute("""
                UPDATE listings SET price=?, miles=?, days_listed=?, is_new=?,
                drop_amount=?, drop_when=?, last_seen=?
                WHERE id=? AND search_id=?
            """, (listing["price"], listing["miles"], listing.get("days_listed"),
                  listing.get("is_new", 0), listing.get("drop_amount"),
                  listing.get("drop_when"), now,
                  listing["id"], listing["search_id"]))
        else:
            self.conn.execute("""
                INSERT INTO listings
                (id, search_id, title, price, miles, city, state, distance,
                 source, url, market, drivetrain, exterior, interior, owners,
                 accidents, days_listed, photos, seller_type, seller_name,
                 seller_rating, vin, drop_amount, drop_when, is_new,
                 first_seen, last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (listing["id"], listing["search_id"], listing.get("title"),
                  listing.get("price"), listing.get("miles"), listing.get("city"),
                  listing.get("state"), listing.get("distance"), listing.get("source"),
                  listing.get("url"), listing.get("market"), listing.get("drivetrain"),
                  listing.get("exterior"), listing.get("interior"), listing.get("owners"),
                  listing.get("accidents"), listing.get("days_listed"), listing.get("photos"),
                  listing.get("seller_type"), listing.get("seller_name"),
                  listing.get("seller_rating"), listing.get("vin"),
                  listing.get("drop_amount"), listing.get("drop_when"),
                  listing.get("is_new", 1), now, now))
        self.conn.commit()

    def get_listings(self, search_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM listings WHERE search_id = ? ORDER BY price ASC",
            (search_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def mark_all_seen(self, search_id: str) -> None:
        self.conn.execute(
            "UPDATE listings SET is_new = 0 WHERE search_id = ?", (search_id,)
        )
        self.conn.commit()

    # ── Save / Hide ───────────────────────────────────────────────────────

    def save_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO saved_listings (user_id, listing_id, saved_at) VALUES (?,?,?)",
            (user_id, listing_id, datetime.now().isoformat())
        )
        self.conn.commit()

    def unsave_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "DELETE FROM saved_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        )
        self.conn.commit()

    def is_saved(self, user_id: str, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM saved_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        ).fetchone()
        return row is not None

    def get_saved_ids(self, user_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT listing_id FROM saved_listings WHERE user_id=?", (user_id,)
        ).fetchall()
        return [r["listing_id"] for r in rows]

    def hide_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO hidden_listings (user_id, listing_id, hidden_at) VALUES (?,?,?)",
            (user_id, listing_id, datetime.now().isoformat())
        )
        self.conn.commit()

    def unhide_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "DELETE FROM hidden_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        )
        self.conn.commit()

    def is_hidden(self, user_id: str, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM hidden_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        ).fetchone()
        return row is not None

    def get_hidden_ids(self, user_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT listing_id FROM hidden_listings WHERE user_id=?", (user_id,)
        ).fetchall()
        return [r["listing_id"] for r in rows]

    def close(self):
        self.conn.close()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()
```

- [ ] **Step 4: Run tests — all 7 must pass**

```bash
pytest tests/test_models.py -v
```

Expected: All 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: full relational database schema (searches, listings, save/hide)"
```

---

## Task 3: Updated Scorer (idealPrice + dealFor)

**Files:**
- Modify: `scorer.py`
- Modify: `tests/test_scorer.py`

The scorer now takes a `search` dict with `ideal_price`/`ideal_miles` in addition to `max_price`/`max_miles`. It also gains a `deal_for(listing)` function using the listing's `market` value.

- [ ] **Step 1: Replace tests/test_scorer.py**

```python
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
    assert score_listing(_listing(19000, 75000), SEARCH) == "good"

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
```

- [ ] **Step 2: Run tests — expect failures on new tests**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && pytest tests/test_scorer.py -v
```

Expected: Several FAIL (wrong signature, missing deal_for).

- [ ] **Step 3: Replace scorer.py**

```python
# scorer.py

def score_listing(listing: dict, search: dict) -> str | None:
    price = listing["price"]
    miles = listing["miles"]
    max_price = search["max_price"]
    max_miles = search["max_miles"]
    ideal_price = search["ideal_price"]
    ideal_miles = search["ideal_miles"]

    if price > max_price or miles > max_miles:
        return None

    if price <= ideal_price and miles <= ideal_miles:
        return "ideal"

    near_price = price > max_price * 0.92
    near_miles = miles > max_miles * 0.92
    if near_price or near_miles:
        return "ok"

    return "good"


def deal_for(listing: dict) -> dict:
    market = listing.get("market") or listing["price"]
    delta = listing["price"] - market
    if delta <= -1200:
        return {"key": "great", "label": "Great deal", "delta": delta}
    if delta <= -300:
        return {"key": "good", "label": "Good price", "delta": delta}
    if delta <= 600:
        return {"key": "fair", "label": "Fair price", "delta": delta}
    return {"key": "high", "label": "Above market", "delta": delta}
```

- [ ] **Step 4: Run tests — all 13 must pass**

```bash
pytest tests/test_scorer.py -v
```

Expected: All 13 PASS.

- [ ] **Step 5: Commit**

```bash
git add scorer.py tests/test_scorer.py
git commit -m "feat: update scorer with idealPrice/idealMiles and deal_for function"
```

---

## Task 4: Marketcheck Scanner — Rich Data + Market Estimate

**Files:**
- Modify: `scanner/marketcheck.py`
- Modify: `scanner/__init__.py`
- Modify: `tests/test_scanner.py`

The scanner now accepts a `search` dict (not global config) and returns rich listing data including market value (computed as median price of all results in this scan).

- [ ] **Step 1: Update tests/test_scanner.py**

Replace the entire file:

```python
# tests/test_scanner.py
import pytest
from unittest.mock import patch, MagicMock
from scanner.marketcheck import fetch_marketcheck_listings
from scanner.playwright_scraper import fetch_playwright_listings
from scanner import run_scan, compute_market_values

SEARCH = {
    "id": "s1", "make": "Toyota", "model": "Highlander", "year": 2016,
    "max_price": 20600, "ideal_price": 18500,
    "max_miles": 130000, "ideal_miles": 90000,
    "zip": "72761", "radius_miles": 300,
    "max_price": 20600, "ideal_price": 18500,
}

FAKE_RESPONSE = {
    "listings": [
        {
            "id": "mc_001", "heading": "2016 Toyota Highlander XLE",
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
    assert r["id"] == "mc_mc_001"
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
    with patch("scanner.playwright_scraper.sync_playwright") as mock_pw:
        mock_pw.side_effect = Exception("browser unavailable")
        result = fetch_playwright_listings(SEARCH)
    assert result == []
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_scanner.py -v
```

Expected: Multiple FAIL.

- [ ] **Step 3: Update scanner/marketcheck.py**

```python
# scanner/marketcheck.py
import requests
from config import MARKETCHECK_API_KEY

BASE_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

SEARCH_ZIPS = [
    "72761", "74101", "64801", "65801",
    "72901", "73101", "72201", "64108",
]

def _fetch_zip(search: dict, zip_code: str) -> list[dict]:
    params = {
        "api_key": MARKETCHECK_API_KEY,
        "year": search["year"],
        "make": search["make"],
        "model": search["model"],
        "price_max": search["max_price"],
        "miles_max": search["max_miles"],
        "zip": zip_code,
        "radius": 100,
        "rows": 100,
        "start": 0,
        "fields": "id,heading,price,miles,dealer,dist,vdp_url,build,extra,dom,media,seller,vin,price_history",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("listings", [])
    except requests.RequestException as e:
        print(f"[marketcheck] {zip_code} error (skipping): {e}")
        return []

def _normalize(item: dict, search_id: str) -> dict:
    build = item.get("build") or {}
    extra = item.get("extra") or {}
    media = item.get("media") or {}
    seller = item.get("seller") or {}
    ph = item.get("price_history") or []

    drop_amount = None
    drop_when = None
    if ph and len(ph) >= 2:
        latest = ph[-1].get("price", 0)
        prev = ph[-2].get("price", 0)
        if prev > latest:
            drop_amount = prev - latest
            drop_when = ph[-1].get("listing_date", "recently")

    seller_type = "Dealer" if seller.get("type") == "D" else "Private"

    return {
        "id": f"mc_{item['id']}",
        "search_id": search_id,
        "title": item.get("heading", ""),
        "price": item.get("price", 0),
        "miles": item.get("miles", 0),
        "city": (item.get("dealer") or {}).get("city", ""),
        "state": (item.get("dealer") or {}).get("state", ""),
        "distance": item.get("dist", 0),
        "source": "marketcheck",
        "url": item.get("vdp_url", ""),
        "market": None,  # filled by compute_market_values
        "drivetrain": build.get("drivetrain", ""),
        "exterior": build.get("ext_color_generic", ""),
        "interior": build.get("int_color_generic", ""),
        "owners": extra.get("owner_count"),
        "accidents": extra.get("accident_cnt"),
        "days_listed": item.get("dom"),
        "photos": len(media.get("photo_links") or []),
        "seller_type": seller_type,
        "seller_name": seller.get("seller_name", ""),
        "seller_rating": seller.get("dealer_rating"),
        "vin": item.get("vin", ""),
        "drop_amount": drop_amount,
        "drop_when": drop_when,
        "is_new": 1,
    }

def fetch_marketcheck_listings(search: dict) -> list[dict]:
    seen_ids = set()
    results = []
    for zip_code in SEARCH_ZIPS:
        for item in _fetch_zip(search, zip_code):
            normalized = _normalize(item, search["id"])
            if normalized["id"] not in seen_ids:
                seen_ids.add(normalized["id"])
                results.append(normalized)
    print(f"[marketcheck] {len(results)} unique listings for {search['make']} {search['model']}")
    return results
```

- [ ] **Step 4: Update scanner/__init__.py**

```python
# scanner/__init__.py
import statistics
from scanner.marketcheck import fetch_marketcheck_listings
from scanner.playwright_scraper import fetch_playwright_listings
from scorer import score_listing

def compute_market_values(listings: list[dict]) -> list[dict]:
    """Set market = median price of all listings in this scan."""
    prices = [l["price"] for l in listings if l.get("price")]
    if not prices:
        return listings
    median = statistics.median(prices)
    return [{**l, "market": int(median)} for l in listings]

def run_scan(search: dict) -> list[dict]:
    """Run a full scan for one search profile. Returns scored listings."""
    listings = fetch_marketcheck_listings(search) + fetch_playwright_listings(search)
    listings = compute_market_values(listings)
    scored = []
    for listing in listings:
        tier = score_listing(listing, search)
        if tier:
            scored.append({**listing, "tier": tier})
    return scored
```

- [ ] **Step 5: Update scanner/playwright_scraper.py to accept search param**

```python
# scanner/playwright_scraper.py
import re
from playwright.sync_api import sync_playwright

def fetch_playwright_listings(search: dict) -> list[dict]:
    try:
        return _scrape_craigslist(search)
    except Exception as e:
        print(f"[playwright] scraper error (skipping): {e}")
        return []

def _scrape_craigslist(search: dict) -> list[dict]:
    markets = [
        ("fayetteville", "nwar"), ("tulsa", "tulsa"),
        ("oklahoma", "oklahoma"), ("springfield", "springfield"),
        ("little rock", "littlerock"),
    ]
    results = []
    query = f"{search['year']}+{search['make']}+{search['model']}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for city, subdomain in markets:
            try:
                url = (
                    f"https://{subdomain}.craigslist.org/search/cta"
                    f"?query={query}&max_price={search['max_price']}"
                    f"&auto_miles_max={search['max_miles']}&sort=date"
                )
                page.goto(url, timeout=15000)
                page.wait_for_selector(".result-row", timeout=8000)
                for item in page.query_selector_all(".result-row")[:20]:
                    try:
                        title_el = item.query_selector(".result-title")
                        price_el = item.query_selector(".result-price")
                        if not title_el or not price_el:
                            continue
                        title = title_el.inner_text().strip()
                        price_text = price_el.inner_text().strip()
                        price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
                        link = title_el.get_attribute("href") or ""
                        listing_id = f"cl_{link.split('/')[-1].replace('.html','')}"
                        results.append({
                            "id": listing_id, "search_id": search["id"],
                            "title": title, "price": price, "miles": 0,
                            "city": city, "state": "", "distance": 0,
                            "source": "craigslist", "url": link,
                            "market": None, "drivetrain": "", "exterior": "",
                            "interior": "", "owners": None, "accidents": None,
                            "days_listed": None, "photos": 0,
                            "seller_type": "Private", "seller_name": "Private seller",
                            "seller_rating": None, "vin": "",
                            "drop_amount": None, "drop_when": None, "is_new": 1,
                        })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[craigslist] {subdomain} failed: {e}")
                continue
        browser.close()
    return results
```

- [ ] **Step 6: Run all scanner tests — must pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: All 3 PASS.

- [ ] **Step 7: Commit**

```bash
git add scanner/ tests/test_scanner.py
git commit -m "feat: enrich scanner with rich listing data and market value estimation"
```

---

## Task 5: Flask REST API — Searches + Listings

**Files:**
- Create: `api/__init__.py`
- Create: `api/searches.py`
- Create: `api/listings.py`
- Create: `api/scan.py`
- Rewrite: `app.py`
- Create: `tests/test_api_searches.py`
- Create: `tests/test_api_listings.py`

- [ ] **Step 1: Write failing API tests**

```python
# tests/test_api_searches.py
import pytest
import json
from app import create_app

@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

HEADERS = {"X-User-Id": "user_test_1", "Content-Type": "application/json"}

def test_create_search(client):
    resp = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["make"] == "Toyota"
    assert data["id"] is not None

def test_list_searches_empty(client):
    resp = client.get("/api/searches", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_list_searches(client):
    client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    resp = client.get("/api/searches", headers=HEADERS)
    assert len(resp.get_json()) == 1

def test_update_search(client):
    create = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    sid = create.get_json()["id"]
    resp = client.put(f"/api/searches/{sid}", headers=HEADERS, json={"max_price": 22000})
    assert resp.status_code == 200
    assert resp.get_json()["max_price"] == 22000

def test_delete_search(client):
    create = client.post("/api/searches", headers=HEADERS, json={
        "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
        "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
        "alert_email": "test@test.com",
    })
    sid = create.get_json()["id"]
    resp = client.delete(f"/api/searches/{sid}", headers=HEADERS)
    assert resp.status_code == 200
    assert client.get("/api/searches", headers=HEADERS).get_json() == []

def test_requires_user_header(client):
    resp = client.get("/api/searches")
    assert resp.status_code == 401
```

```python
# tests/test_api_listings.py
import pytest
from app import create_app

@pytest.fixture
def client_with_search(tmp_path):
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        headers = {"X-User-Id": "user_test_1", "Content-Type": "application/json"}
        r = c.post("/api/searches", headers=headers, json={
            "make": "Toyota", "model": "Highlander", "trim": "", "year": 2016,
            "max_price": 20600, "ideal_price": 18500, "max_miles": 130000, "ideal_miles": 90000,
            "zip": "72761", "city": "Siloam Springs, AR", "radius_miles": 300, "interval_hours": 2,
            "alert_email": "test@test.com",
        })
        search_id = r.get_json()["id"]
        yield c, search_id, headers

def test_listings_empty(client_with_search):
    client, sid, headers = client_with_search
    resp = client.get(f"/api/searches/{sid}/listings", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_save_and_unsave(client_with_search):
    client, sid, headers = client_with_search
    resp = client.post("/api/listings/mc_abc/save", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["saved"] is True
    resp2 = client.delete("/api/listings/mc_abc/save", headers=headers)
    assert resp2.get_json()["saved"] is False

def test_hide_and_unhide(client_with_search):
    client, sid, headers = client_with_search
    resp = client.post("/api/listings/mc_abc/hide", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["hidden"] is True
    resp2 = client.delete("/api/listings/mc_abc/hide", headers=headers)
    assert resp2.get_json()["hidden"] is False
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_api_searches.py tests/test_api_listings.py -v
```

Expected: ImportError (no create_app).

- [ ] **Step 3: Create api/__init__.py**

```python
# api/__init__.py
from flask import Blueprint

def register_blueprints(app):
    from api.searches import searches_bp
    from api.listings import listings_bp
    from api.scan import scan_bp
    app.register_blueprint(searches_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(scan_bp)
```

- [ ] **Step 4: Create api/searches.py**

```python
# api/searches.py
from flask import Blueprint, request, jsonify, g

searches_bp = Blueprint("searches", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@searches_bp.route("/api/searches", methods=["GET"])
def list_searches():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    searches = g.db.list_searches(user_id)
    return jsonify(searches)

@searches_bp.route("/api/searches", methods=["POST"])
def create_search():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    data["user_id"] = user_id
    required = ["make", "model", "year", "max_price", "ideal_price",
                "max_miles", "ideal_miles", "zip", "city", "alert_email"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    search = g.db.create_search(data)
    return jsonify(search), 201

@searches_bp.route("/api/searches/<search_id>", methods=["GET"])
def get_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    return jsonify(search)

@searches_bp.route("/api/searches/<search_id>", methods=["PUT"])
def update_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    updated = g.db.update_search(search_id, request.get_json())
    return jsonify(updated)

@searches_bp.route("/api/searches/<search_id>", methods=["DELETE"])
def delete_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    g.db.delete_search(search_id)
    return jsonify({"deleted": True})
```

- [ ] **Step 5: Create api/listings.py**

```python
# api/listings.py
from flask import Blueprint, request, jsonify, g

listings_bp = Blueprint("listings", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@listings_bp.route("/api/searches/<search_id>/listings", methods=["GET"])
def get_listings(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    listings = g.db.get_listings(search_id)
    saved_ids = set(g.db.get_saved_ids(user_id))
    hidden_ids = set(g.db.get_hidden_ids(user_id))
    from scorer import score_listing, deal_for
    result = []
    for l in listings:
        if l["id"] in hidden_ids:
            continue
        tier = score_listing(l, search)
        if not tier:
            continue
        deal = deal_for(l)
        result.append({
            **l,
            "tier": tier,
            "deal": deal,
            "saved": l["id"] in saved_ids,
        })
    result.sort(key=lambda x: (["ideal","good","ok"].index(x["tier"]), x["deal"]["delta"], x["price"]))
    return jsonify(result)

@listings_bp.route("/api/listings/<listing_id>/save", methods=["POST"])
def save_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.save_listing(user_id, listing_id)
    return jsonify({"saved": True})

@listings_bp.route("/api/listings/<listing_id>/save", methods=["DELETE"])
def unsave_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.unsave_listing(user_id, listing_id)
    return jsonify({"saved": False})

@listings_bp.route("/api/listings/<listing_id>/hide", methods=["POST"])
def hide_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.hide_listing(user_id, listing_id)
    return jsonify({"hidden": True})

@listings_bp.route("/api/listings/<listing_id>/hide", methods=["DELETE"])
def unhide_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.unhide_listing(user_id, listing_id)
    return jsonify({"hidden": False})
```

- [ ] **Step 6: Create api/scan.py**

```python
# api/scan.py
import threading
from flask import Blueprint, request, jsonify, g

scan_bp = Blueprint("scan", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@scan_bp.route("/api/scan", methods=["POST"])
def scan_all():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    from scheduler import trigger_scan_for_user
    threading.Thread(target=trigger_scan_for_user, args=(user_id,), daemon=True).start()
    return jsonify({"status": "scan started"})

@scan_bp.route("/api/searches/<search_id>/scan", methods=["POST"])
def scan_one(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    from scheduler import trigger_scan_for_search
    threading.Thread(target=trigger_scan_for_search, args=(search,), daemon=True).start()
    return jsonify({"status": "scan started"})

@scan_bp.route("/api/status", methods=["GET"])
def status():
    from scheduler import get_status
    return jsonify(get_status())
```

- [ ] **Step 7: Rewrite app.py**

```python
# app.py
import os
import threading
from flask import Flask, g
from flask_cors import CORS
from models import Database

_db_lock = threading.Lock()
_db_instance = None

def get_db(db_path: str = None) -> Database:
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = Database(db_path or os.environ.get("DB_PATH", "carfinder.db"))
    return _db_instance

def create_app(db_path: str = None) -> Flask:
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            os.environ.get("FRONTEND_URL", ""),
        ],
        "allow_headers": ["Content-Type", "X-User-Id", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    }})

    db = Database(db_path or os.environ.get("DB_PATH", "carfinder.db"))

    @app.before_request
    def attach_db():
        g.db = db

    from api import register_blueprints
    register_blueprints(app)

    return app

app = create_app()
```

- [ ] **Step 8: Run API tests — all must pass**

```bash
pytest tests/test_api_searches.py tests/test_api_listings.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 9: Commit**

```bash
git add api/ app.py tests/test_api_searches.py tests/test_api_listings.py
git commit -m "feat: REST API for searches and listings with save/hide"
```

---

## Task 6: Multi-Search Scheduler

**Files:**
- Rewrite: `scheduler.py`

- [ ] **Step 1: Rewrite scheduler.py**

```python
# scheduler.py
import os
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, get_db
from scanner import run_scan
from email_alert import send_alert
from config import SEARCH as DEFAULT_SEARCH

_status = {"scanning": False, "last_scan": None, "next_scan": None}
_status_lock = threading.Lock()

def get_status() -> dict:
    with _status_lock:
        return dict(_status)

def _set_status(**kwargs):
    with _status_lock:
        _status.update(kwargs)

def trigger_scan_for_search(search: dict) -> None:
    """Scan one search profile, persist results, send alert for new matches."""
    db = get_db()
    print(f"[scheduler] Scanning: {search['make']} {search['model']} (id={search['id']})")
    _set_status(scanning=True)
    try:
        listings = run_scan(search)
        new_listings = []
        for listing in listings:
            existing = db.conn.execute(
                "SELECT id, is_new FROM listings WHERE id=? AND search_id=?",
                (listing["id"], search["id"])
            ).fetchone()
            listing["is_new"] = 0 if existing else 1
            db.upsert_listing(listing)
            if not existing:
                new_listings.append(listing)

        print(f"[scheduler] {len(listings)} total, {len(new_listings)} new for search {search['id']}")
        if new_listings:
            send_alert(search, new_listings)
    except Exception as e:
        print(f"[scheduler] Error scanning {search['id']}: {e}")
    finally:
        _set_status(
            scanning=False,
            last_scan=datetime.now().isoformat(),
        )

def trigger_scan_for_user(user_id: str) -> None:
    """Scan all active searches for a given user."""
    db = get_db()
    searches = db.list_searches(user_id)
    for search in searches:
        trigger_scan_for_search(search)

def _run_all_active_searches() -> None:
    """Scheduled job: scan every active search across all users."""
    db = get_db()
    searches = db.list_all_active_searches()
    print(f"[scheduler] Scheduled scan — {len(searches)} active searches")
    for search in searches:
        trigger_scan_for_search(search)

def start():
    flask_app = create_app()
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_all_active_searches, "interval", hours=2, id="scan_all")
    scheduler.start()
    print("[scheduler] APScheduler started. Running initial scan...")
    threading.Thread(target=_run_all_active_searches, daemon=True).start()
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start()
```

- [ ] **Step 2: Verify scheduler imports cleanly**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && python3 -c "import scheduler; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scheduler.py
git commit -m "feat: multi-search scheduler with per-search and per-user scan triggers"
```

---

## Task 7: Updated Email Alert (Multi-Search)

**Files:**
- Modify: `email_alert.py`
- Modify: `tests/test_email_alert.py`

- [ ] **Step 1: Update tests/test_email_alert.py**

```python
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
```

- [ ] **Step 2: Run to verify some fail**

```bash
pytest tests/test_email_alert.py -v
```

Expected: Several FAIL (wrong signature).

- [ ] **Step 3: Rewrite email_alert.py**

```python
# email_alert.py
import resend
from config import RESEND_API_KEY, RESEND_FROM

TIER_LABELS = {"ideal": "⭐ IDEAL", "good": "✓ GOOD", "ok": "~ OK"}
TIER_ORDER = ["ideal", "good", "ok"]

def build_email_body(search: dict, listings: list[dict]) -> str:
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    grouped = {tier: [] for tier in TIER_ORDER}
    for listing in listings:
        tier = listing.get("tier", "ok")
        grouped[tier].append(listing)

    lines = [f"{len(listings)} new match(es) for your {vehicle} search.\n"]
    for tier in TIER_ORDER:
        group = grouped[tier]
        if not group:
            continue
        lines.append(f"\n{'='*40}")
        lines.append(f"{TIER_LABELS[tier]} ({len(group)} listing{'s' if len(group)!=1 else ''})")
        lines.append("="*40)
        for l in group:
            deal = l.get("deal") or {}
            deal_str = f"  Deal:     {deal.get('label','')} (${abs(deal.get('delta',0)):,} {'below' if deal.get('delta',0)<0 else 'above'} market)\n" if deal.get("label") else ""
            lines.append(
                f"\n{l['title']}\n"
                f"  Price:    ${l['price']:,}\n"
                f"  Mileage:  {l['miles']:,} mi\n"
                f"  Location: {l['city']}, {l['state']} ({l['distance']:.0f} mi away)\n"
                f"  Source:   {l['source']}\n"
                f"{deal_str}"
                f"  Link:     {l['url']}\n"
            )
    return "\n".join(lines)

def send_alert(search: dict, listings: list[dict]) -> None:
    if not listings:
        return
    resend.api_key = RESEND_API_KEY
    body = build_email_body(search, listings)
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    n = len(listings)
    subject = f"[CarFinder] {n} new {search['model']} match{'es' if n!=1 else ''} found"
    resend.Emails.send({
        "from": RESEND_FROM,
        "to": search["alert_email"],
        "subject": subject,
        "text": body,
    })
    print(f"[email] Sent: {subject} → {search['alert_email']}")
```

- [ ] **Step 4: Run all tests — all must pass**

```bash
pytest tests/ -v
```

Expected: All tests PASS (models, scorer, scanner, api, email).

- [ ] **Step 5: Commit**

```bash
git add email_alert.py tests/test_email_alert.py
git commit -m "feat: multi-search email alert with deal signals"
```

---

## Task 8: Seed the Default Search + Smoke Test

**Files:**
- Create: `seed.py`

This seeds the database with the user's real Highlander search so the app works immediately on Railway.

- [ ] **Step 1: Create seed.py**

```python
# seed.py
"""One-time seed: creates the default Highlander search for user_marcos."""
from models import Database

db = Database()
existing = db.list_searches("user_marcos")
if existing:
    print("Already seeded.")
else:
    s = db.create_search({
        "user_id": "user_marcos",
        "make": "Toyota", "model": "Highlander", "trim": "",
        "year": 2016, "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_email": "marcosrrez@gmail.com",
    })
    print(f"Seeded search: {s['id']}")
db.close()
```

- [ ] **Step 2: Run seed**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && python3 seed.py
```

Expected: `Seeded search: <some-id>`

- [ ] **Step 3: Smoke test the API**

```bash
source venv/bin/activate && python3 -c "
from app import create_app
app = create_app()
with app.test_client() as c:
    r = c.get('/api/searches', headers={'X-User-Id': 'user_marcos'})
    print('Searches:', r.get_json())
"
```

Expected: Prints the seeded search.

- [ ] **Step 4: Commit and deploy to Railway**

```bash
git add seed.py
git commit -m "feat: seed script for default search"
source "$HOME/.railway/env"
railway up --detach
```

---

## Task 9: Run Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
cd /Users/marcos/carfinder && source venv/bin/activate && pytest tests/ -v --tb=short
```

Expected: All tests PASS. Count should be ~35+.

- [ ] **Step 2: Final commit**

```bash
git add .
git commit -m "feat: Plan A complete — full REST API backend"
```
