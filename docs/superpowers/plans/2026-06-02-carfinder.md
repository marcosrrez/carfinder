# CarFinder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a car listing scanner that checks 5 sources every 2 hours, emails new matches to the user, and shows a live Flask dashboard.

**Architecture:** A Python app with a Marketcheck API client for dealer sites, a Playwright scraper for Facebook Marketplace and Craigslist, SQLite for deduplication, Gmail SMTP for alerts, and a Flask dashboard serving a `results.json` file updated each scan. APScheduler runs the scan loop in a background thread.

**Tech Stack:** Python 3.11+, Flask, APScheduler, Playwright, Requests, SQLite (stdlib), smtplib (stdlib)

---

## File Structure

```
carfinder/
├── .env                          # API keys + Gmail credentials (never commit)
├── .env.example                  # Safe template to commit
├── requirements.txt
├── config.py                     # Search profile + env loading
├── scorer.py                     # Tier scoring logic (Ideal / Good / Ok)
├── db.py                         # SQLite deduplication store
├── scanner/
│   ├── __init__.py               # run_scan() entry point
│   ├── marketcheck.py            # Marketcheck API → normalized listings
│   └── playwright_scraper.py     # Facebook Marketplace + Craigslist
├── email_alert.py                # Gmail SMTP alert sender
├── app.py                        # Flask dashboard + Scan Now endpoint
├── scheduler.py                  # APScheduler loop + main entry point
├── templates/
│   └── dashboard.html            # Dashboard UI
├── static/
│   └── style.css                 # Dashboard styles
├── results.json                  # Auto-generated, gitignored
└── tests/
    ├── test_scorer.py
    ├── test_db.py
    ├── test_email_alert.py
    └── test_scanner.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.env`
- Create: `config.py`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
flask==3.0.3
apscheduler==3.10.4
playwright==1.44.0
requests==2.32.3
python-dotenv==1.0.1
pytest==8.2.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd /Users/marcos/carfinder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Expected: All packages install without errors.

- [ ] **Step 3: Create .env.example**

```bash
# .env.example
MARKETCHECK_API_KEY=your_key_here
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
ALERT_EMAIL=marcosrrez@gmail.com
```

- [ ] **Step 4: Create .env with real values**

Get a free Marketcheck API key at https://marketcheck.com (sign up → API keys).
Get a Gmail App Password: Google Account → Security → 2FA → App Passwords → generate one named "CarFinder".

```bash
# .env  (never commit this file)
MARKETCHECK_API_KEY=<your_real_key>
GMAIL_USER=<your_gmail>
GMAIL_APP_PASSWORD=<your_app_password>
ALERT_EMAIL=marcosrrez@gmail.com
```

- [ ] **Step 5: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

MARKETCHECK_API_KEY = os.environ["MARKETCHECK_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ALERT_EMAIL = os.environ["ALERT_EMAIL"]

SEARCH = {
    "make": "Toyota",
    "model": "Highlander",
    "year": 2016,
    "max_price": 20600,
    "max_miles": 130000,
    "zip": "72761",       # Siloam Springs AR
    "radius_miles": 300,
    "scan_interval_hours": 2,
}

IDEAL = {"max_price": 18500, "max_miles": 90000}
GOOD  = {"max_price": 20600, "max_miles": 80000}
```

- [ ] **Step 6: Create .gitignore**

```
venv/
.env
results.json
*.pyc
__pycache__/
.DS_Store
```

- [ ] **Step 7: Initialize git and commit**

```bash
git init
git add requirements.txt .env.example config.py .gitignore
git commit -m "feat: project setup and config"
```

---

## Task 2: Scorer

**Files:**
- Create: `scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scorer.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scorer.py -v
```

Expected: `ImportError: No module named 'scorer'`

- [ ] **Step 3: Implement scorer.py**

```python
# scorer.py
from config import SEARCH, IDEAL, GOOD

def score_listing(listing: dict) -> str | None:
    price = listing["price"]
    miles = listing["miles"]

    if price > SEARCH["max_price"] or miles > SEARCH["max_miles"]:
        return None

    if price <= IDEAL["max_price"] and miles <= IDEAL["max_miles"]:
        return "ideal"

    if price <= GOOD["max_price"] and miles <= GOOD["max_miles"]:
        return "good"

    return "ok"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scorer.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scorer.py tests/test_scorer.py
git commit -m "feat: listing tier scorer (ideal/good/ok)"
```

---

## Task 3: Deduplication Database

**Files:**
- Create: `db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_db.py
import pytest
import tempfile
import os
from db import ListingDB

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = ListingDB(path)
    yield d
    os.unlink(path)

def test_new_listing_not_seen(db):
    assert db.is_new("abc123") is True

def test_seen_listing_after_mark(db):
    db.mark_seen("abc123")
    assert db.is_new("abc123") is False

def test_filter_new_keeps_unseen(db):
    listings = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    db.mark_seen("b")
    result = db.filter_new(listings)
    assert [l["id"] for l in result] == ["a", "c"]

def test_filter_new_marks_as_seen(db):
    listings = [{"id": "x"}]
    db.filter_new(listings)
    assert db.is_new("x") is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_db.py -v
```

Expected: `ImportError: No module named 'db'`

- [ ] **Step 3: Implement db.py**

```python
# db.py
import sqlite3

class ListingDB:
    def __init__(self, path: str = "carfinder.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)"
        )
        self.conn.commit()

    def is_new(self, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM seen WHERE id = ?", (listing_id,)
        ).fetchone()
        return row is None

    def mark_seen(self, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen (id) VALUES (?)", (listing_id,)
        )
        self.conn.commit()

    def filter_new(self, listings: list[dict]) -> list[dict]:
        new = [l for l in listings if self.is_new(l["id"])]
        for l in new:
            self.mark_seen(l["id"])
        return new
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: SQLite deduplication store"
```

---

## Task 4: Marketcheck API Scanner

**Files:**
- Create: `scanner/__init__.py`
- Create: `scanner/marketcheck.py`
- Create: `tests/test_scanner.py` (partial — marketcheck section)

- [ ] **Step 1: Write failing test using a mock response**

```python
# tests/test_scanner.py
import pytest
from unittest.mock import patch, MagicMock
from scanner.marketcheck import fetch_marketcheck_listings

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
            "price": 25000,   # over budget — should be excluded by API params
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
    assert results[0]["id"] == "mc_001"
    assert results[0]["price"] == 17995
    assert results[0]["miles"] == 89200
    assert results[0]["city"] == "Fayetteville"
    assert results[0]["state"] == "AR"
    assert results[0]["distance"] == 28.3
    assert results[0]["source"] == "marketcheck"
    assert results[0]["url"] == "https://example.com/listing/mc_001"
    assert results[0]["title"] == "2016 Toyota Highlander XLE"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py::test_fetch_returns_normalized_listings -v
```

Expected: `ImportError: No module named 'scanner.marketcheck'`

- [ ] **Step 3: Create scanner/__init__.py**

```python
# scanner/__init__.py
from scanner.marketcheck import fetch_marketcheck_listings
from scanner.playwright_scraper import fetch_playwright_listings
from scorer import score_listing

def run_scan() -> list[dict]:
    listings = fetch_marketcheck_listings() + fetch_playwright_listings()
    scored = []
    for l in listings:
        tier = score_listing(l)
        if tier:
            scored.append({**l, "score": tier})
    return scored
```

- [ ] **Step 4: Implement scanner/marketcheck.py**

```python
# scanner/marketcheck.py
import requests
from config import MARKETCHECK_API_KEY, SEARCH

BASE_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

def fetch_marketcheck_listings() -> list[dict]:
    params = {
        "api_key": MARKETCHECK_API_KEY,
        "year": SEARCH["year"],
        "make": SEARCH["make"],
        "model": SEARCH["model"],
        "price_max": SEARCH["max_price"],
        "miles_max": SEARCH["max_miles"],
        "zip": SEARCH["zip"],
        "radius": SEARCH["radius_miles"],
        "rows": 100,
        "start": 0,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("listings", []):
        results.append({
            "id": f"mc_{item['id']}",
            "title": item.get("heading", ""),
            "price": item.get("price", 0),
            "miles": item.get("miles", 0),
            "city": item.get("dealer", {}).get("city", ""),
            "state": item.get("dealer", {}).get("state", ""),
            "distance": item.get("dist", 0),
            "source": "marketcheck",
            "url": item.get("vdp_url", ""),
        })
    return results
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_scanner.py::test_fetch_returns_normalized_listings -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scanner/ tests/test_scanner.py
git commit -m "feat: Marketcheck API scanner"
```

---

## Task 5: Playwright Scraper (Facebook Marketplace + Craigslist)

**Files:**
- Create: `scanner/playwright_scraper.py`

Note: Facebook Marketplace requires login and is heavily protected. We implement a best-effort scraper with graceful fallback (returns empty list on failure). Craigslist is more scraper-friendly.

- [ ] **Step 1: Add scraper test**

Add this to `tests/test_scanner.py`:

```python
from scanner.playwright_scraper import fetch_playwright_listings

def test_playwright_returns_list_on_failure():
    # Scraper should never crash the scan — returns [] on any error
    # We can't integration-test browser scraping in unit tests,
    # so we verify the error handling path.
    with patch("scanner.playwright_scraper.sync_playwright") as mock_pw:
        mock_pw.side_effect = Exception("browser unavailable")
        result = fetch_playwright_listings()
    assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py::test_playwright_returns_list_on_failure -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement scanner/playwright_scraper.py**

```python
# scanner/playwright_scraper.py
import re
from playwright.sync_api import sync_playwright
from config import SEARCH

def fetch_playwright_listings() -> list[dict]:
    try:
        results = []
        results += _scrape_craigslist()
        return results
    except Exception as e:
        print(f"[playwright] scraper error (skipping): {e}")
        return []

def _scrape_craigslist() -> list[dict]:
    # Craigslist uses subdomain per city; we hit the nearest large markets
    markets = [
        ("fayetteville", "nwar"),
        ("tulsa", "tulsa"),
        ("oklahoma", "oklahoma"),
        ("springfield", "springfield"),
        ("little rock", "littlerock"),
    ]
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for city, subdomain in markets:
            try:
                url = (
                    f"https://{subdomain}.craigslist.org/search/cta"
                    f"?query=2016+toyota+highlander"
                    f"&max_price={SEARCH['max_price']}"
                    f"&auto_miles_max={SEARCH['max_miles']}"
                    f"&sort=date"
                )
                page.goto(url, timeout=15000)
                page.wait_for_selector(".result-row", timeout=8000)
                items = page.query_selector_all(".result-row")
                for item in items[:20]:
                    try:
                        title_el = item.query_selector(".result-title")
                        price_el = item.query_selector(".result-price")
                        if not title_el or not price_el:
                            continue
                        title = title_el.inner_text().strip()
                        price_text = price_el.inner_text().strip()
                        price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
                        link = title_el.get_attribute("href") or ""
                        listing_id = f"cl_{link.split('/')[-1].replace('.html', '')}"
                        results.append({
                            "id": listing_id,
                            "title": title,
                            "price": price,
                            "miles": 0,   # Craigslist mileage is in body text; skip for now
                            "city": city,
                            "state": "",
                            "distance": 0,
                            "source": "craigslist",
                            "url": link,
                        })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[craigslist] {subdomain} failed: {e}")
                continue
        browser.close()
    return results
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_scanner.py::test_playwright_returns_list_on_failure -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scanner/playwright_scraper.py tests/test_scanner.py
git commit -m "feat: Craigslist playwright scraper with graceful fallback"
```

---

## Task 6: Email Alert

**Files:**
- Create: `email_alert.py`
- Create: `tests/test_email_alert.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_email_alert.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_email_alert.py -v
```

Expected: `ImportError: No module named 'email_alert'`

- [ ] **Step 3: Implement email_alert.py**

```python
# email_alert.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_EMAIL, SEARCH

TIER_LABELS = {"ideal": "⭐ IDEAL", "good": "✓ GOOD", "ok": "~ OK"}
TIER_ORDER = ["ideal", "good", "ok"]

def build_email_body(listings: list[dict]) -> str:
    grouped = {tier: [] for tier in TIER_ORDER}
    for l in listings:
        grouped[l["score"]].append(l)

    lines = [f"{len(listings)} new match(es) for your {SEARCH['year']} {SEARCH['make']} {SEARCH['model']} search.\n"]
    for tier in TIER_ORDER:
        group = grouped[tier]
        if not group:
            continue
        lines.append(f"\n{'='*40}")
        lines.append(f"{TIER_LABELS[tier]} ({len(group)} listing{'s' if len(group) != 1 else ''})")
        lines.append("="*40)
        for l in group:
            lines.append(
                f"\n{l['title']}\n"
                f"  Price:    ${l['price']:,}\n"
                f"  Mileage:  {l['miles']:,} mi\n"
                f"  Location: {l['city']}, {l['state']} ({l['distance']:.0f} mi away)\n"
                f"  Source:   {l['source']}\n"
                f"  Link:     {l['url']}\n"
            )
    return "\n".join(lines)

def send_alert(listings: list[dict]) -> None:
    if not listings:
        return

    body = build_email_body(listings)
    subject = f"[CarFinder] {len(listings)} new {SEARCH['model']} match{'es' if len(listings) != 1 else ''} found"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ALERT_EMAIL
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, ALERT_EMAIL, msg.as_string())
    print(f"[email] Sent alert: {subject}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_email_alert.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add email_alert.py tests/test_email_alert.py
git commit -m "feat: Gmail SMTP email alert with tier grouping"
```

---

## Task 7: Flask Dashboard

**Files:**
- Create: `app.py`
- Create: `templates/dashboard.html`
- Create: `static/style.css`

- [ ] **Step 1: Create app.py**

```python
# app.py
import json
import os
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__)
_scan_lock = threading.Lock()
RESULTS_FILE = "results.json"

def load_results() -> dict:
    if not os.path.exists(RESULTS_FILE):
        return {"listings": [], "last_scan": None, "next_scan": None, "total": 0, "new_count": 0}
    with open(RESULTS_FILE) as f:
        return json.load(f)

def save_results(listings: list[dict], new_count: int, next_scan_iso: str) -> None:
    data = {
        "listings": listings,
        "last_scan": datetime.now().isoformat(),
        "next_scan": next_scan_iso,
        "total": len(listings),
        "new_count": new_count,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def dashboard():
    return render_template("dashboard.html", **load_results())

@app.route("/api/results")
def api_results():
    return jsonify(load_results())

@app.route("/api/scan", methods=["POST"])
def scan_now():
    from scheduler import trigger_scan
    threading.Thread(target=trigger_scan, daemon=True).start()
    return jsonify({"status": "scan started"})
```

- [ ] **Step 2: Create templates/dashboard.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CarFinder Dashboard</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <nav class="topbar">
    <span class="brand">🚗 CarFinder</span>
    <span class="email">marcosrrez@gmail.com</span>
  </nav>

  <div class="container">
    <div class="profile-card">
      <div class="profile-header">
        <span>Your Search</span>
        <span class="badge active">● ACTIVE</span>
      </div>
      <div class="profile-grid">
        <div><label>VEHICLE</label><strong>2016 Toyota Highlander</strong></div>
        <div><label>MAX PRICE</label><strong>$20,600</strong></div>
        <div><label>MAX MILES</label><strong>130,000</strong></div>
        <div><label>RADIUS</label><strong>300 mi · Siloam Springs AR</strong></div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-number blue">{{ total }}</div>
        <div class="stat-label">Total Matches Found</div>
      </div>
      <div class="stat-card">
        <div class="stat-number green">{{ new_count }}</div>
        <div class="stat-label">New Since Last Alert</div>
      </div>
    </div>

    <div class="listings-section">
      <div class="section-title">LATEST MATCHES</div>
      {% for l in listings %}
      <div class="listing-card {{ l.score }}">
        <div class="listing-left">
          <span class="tier-badge {{ l.score }}">
            {% if l.score == 'ideal' %}⭐ IDEAL{% elif l.score == 'good' %}✓ GOOD{% else %}~ OK{% endif %}
          </span>
          <span class="listing-title">{{ l.title }}</span>
          <div class="listing-meta">{{ "{:,}".format(l.miles) }} mi · {{ l.city }}, {{ l.state }} · {{ "%.0f"|format(l.distance) }} mi away · {{ l.source }}</div>
        </div>
        <div class="listing-right">
          <div class="listing-price {{ l.score }}">${{ "{:,}".format(l.price) }}</div>
          <a href="{{ l.url }}" target="_blank" class="view-link">View Listing →</a>
        </div>
      </div>
      {% else %}
      <div class="empty-state">No matches yet — scan is running every 2 hours.</div>
      {% endfor %}
    </div>

    <div class="footer-bar">
      <span>
        {% if last_scan %}Last scan: {{ last_scan[:16].replace('T', ' ') }}{% else %}No scan yet{% endif %}
      </span>
      <button class="scan-btn" onclick="scanNow()">Scan Now</button>
    </div>
  </div>

  <script>
    function scanNow() {
      fetch('/api/scan', {method: 'POST'})
        .then(() => { setTimeout(() => location.reload(), 8000); });
    }
  </script>
</body>
</html>
```

- [ ] **Step 3: Create static/style.css**

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; }

.topbar { background: #161b22; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; }
.brand { font-weight: 700; font-size: 16px; color: #58a6ff; }
.email { color: #8b949e; font-size: 12px; }

.container { max-width: 900px; margin: 24px auto; padding: 0 20px; display: flex; flex-direction: column; gap: 16px; }

.profile-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
.profile-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 600; }
.badge.active { background: #238636; color: #fff; font-size: 10px; padding: 3px 10px; border-radius: 12px; }
.profile-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.profile-grid label { display: block; color: #8b949e; font-size: 10px; letter-spacing: 1px; margin-bottom: 3px; }

.stats-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }
.stat-number { font-size: 32px; font-weight: 700; }
.stat-number.blue { color: #58a6ff; }
.stat-number.green { color: #3fb950; }
.stat-label { color: #8b949e; font-size: 11px; margin-top: 4px; }

.section-title { color: #8b949e; font-size: 10px; letter-spacing: 1px; margin-bottom: 10px; }

.listing-card { background: #161b22; border-radius: 8px; padding: 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
.listing-card.ideal { border: 1px solid #238636; }
.listing-card.good { border: 1px solid #1f6feb; }
.listing-card.ok { border: 1px solid #9e6a03; }

.tier-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; margin-right: 8px; }
.tier-badge.ideal { background: #1a4429; color: #3fb950; }
.tier-badge.good { background: #1c2c4a; color: #58a6ff; }
.tier-badge.ok { background: #2d1f0a; color: #d29922; }

.listing-title { font-weight: 600; }
.listing-meta { color: #8b949e; font-size: 11px; margin-top: 4px; }
.listing-right { text-align: right; }
.listing-price { font-size: 20px; font-weight: 700; }
.listing-price.ideal { color: #3fb950; }
.listing-price.good, .listing-price.ok { color: #e6edf3; }
.view-link { color: #58a6ff; font-size: 11px; text-decoration: none; }

.footer-bar { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; color: #8b949e; font-size: 12px; }
.scan-btn { background: #21262d; border: 1px solid #30363d; color: #e6edf3; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; }
.scan-btn:hover { background: #30363d; }
.empty-state { color: #8b949e; text-align: center; padding: 40px; }
```

- [ ] **Step 4: Commit**

```bash
git add app.py templates/ static/
git commit -m "feat: Flask dashboard with listing cards and scan-now button"
```

---

## Task 8: Scheduler + Main Entry Point

**Files:**
- Create: `scheduler.py`

- [ ] **Step 1: Implement scheduler.py**

```python
# scheduler.py
import json
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import run_scan
from db import ListingDB
from email_alert import send_alert
from app import app, save_results
from config import SEARCH

db = ListingDB()
_next_scan_time = None

def trigger_scan():
    global _next_scan_time
    print(f"[scheduler] Running scan at {datetime.now().strftime('%H:%M:%S')}")
    try:
        all_listings = run_scan()
        new_listings = db.filter_new(all_listings)
        print(f"[scheduler] Found {len(all_listings)} total, {len(new_listings)} new")
        send_alert(new_listings)
        interval = SEARCH["scan_interval_hours"]
        _next_scan_time = datetime.now() + timedelta(hours=interval)
        save_results(all_listings, len(new_listings), _next_scan_time.isoformat())
    except Exception as e:
        print(f"[scheduler] Scan error: {e}")

def start():
    interval_hours = SEARCH["scan_interval_hours"]
    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger_scan, "interval", hours=interval_hours, id="scan")
    scheduler.start()
    print(f"[scheduler] Scan scheduled every {interval_hours}h. Running first scan now...")
    threading.Thread(target=trigger_scan, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)

if __name__ == "__main__":
    start()
```

- [ ] **Step 2: Run a smoke test**

```bash
cd /Users/marcos/carfinder
source venv/bin/activate
python scheduler.py
```

Expected output:
```
[scheduler] Scan scheduled every 2h. Running first scan now...
[scheduler] Running scan at HH:MM:SS
[scheduler] Found N total, M new
 * Running on http://0.0.0.0:5001
```

Open http://localhost:5001 in browser — dashboard should load.

- [ ] **Step 3: Commit**

```bash
git add scheduler.py
git commit -m "feat: APScheduler loop + Flask app entry point"
```

---

## Task 9: Run Full Test Suite and Verify

- [ ] **Step 1: Run all tests**

```bash
cd /Users/marcos/carfinder
source venv/bin/activate
pytest tests/ -v
```

Expected: All tests PASS (scorer, db, scanner mock, email mock).

- [ ] **Step 2: Start the app and do a live scan**

```bash
python scheduler.py
```

- Open http://localhost:5001
- Click "Scan Now"
- Wait ~10 seconds, refresh page
- Verify listings appear with correct color-coding
- Check marcosrrez@gmail.com for alert email

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: CarFinder v1 complete — scanner, dashboard, email alerts"
```

---

## Notes

- **Marketcheck free tier:** 500 API calls/month. At 2hr intervals × 5 days = 60 calls. Well within limit.
- **Gmail App Password:** Required since Google disabled less-secure app access. Generate at: Google Account → Security → 2-Step Verification → App passwords.
- **Facebook Marketplace:** Not included in v1 scraper (requires login + anti-bot measures). Craigslist is included. Add FB later if needed.
- **results.json** is gitignored — it's ephemeral scan output.
