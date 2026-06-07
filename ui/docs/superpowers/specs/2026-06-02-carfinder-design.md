# CarFinder — Design Spec
Date: 2026-06-02

## Overview

CarFinder is a car listing scanner and alert app. Users configure a vehicle search profile (make, model, year, max price, max mileage, radius, location) and the system scans multiple listing sources every N hours, emails new matches, and shows a live dashboard.

The first user (guinea pig) is searching for a **2016 Toyota Highlander** under **$20,600**, under **130,000 miles**, within **300 miles of Siloam Springs, AR**, scanning every **2 hours**, alerting to **marcosrrez@gmail.com**.

---

## Search Criteria & Scoring

Each listing is scored into one of three tiers:

| Tier | Label | Criteria |
|------|-------|----------|
| ⭐ Ideal | Green | Price ≤ $18,500 AND miles ≤ 90,000 |
| ✓ Good | Blue | Price ≤ $20,600 AND miles ≤ 80,000 |
| ~ Ok | Yellow | Price ≤ $20,600 AND miles ≤ 130,000 |

Listings outside all tiers are discarded.

---

## Data Sources

| Source | Method | Coverage |
|--------|--------|----------|
| CarGurus | Marketcheck API | Dealers |
| AutoTrader | Marketcheck API | Dealers |
| Cars.com | Marketcheck API | Dealers |
| Facebook Marketplace | Playwright scraper | Private sellers |
| Craigslist | Playwright scraper | Private sellers |

**Marketcheck API** (free tier: 500 calls/month) handles dealer inventory reliably without scraping risk. Playwright handles private seller platforms.

---

## Architecture

```
Scheduler (APScheduler, every 2hrs)
  └── Scanner Engine
        ├── Marketcheck API → filter → deduplicate
        └── Playwright scraper (FB + Craigslist) → filter → deduplicate
  └── Deduplication (SQLite: seen listing IDs)
  └── Email Alert (Gmail SMTP, only if new matches found)
  └── Dashboard update (flat JSON file served by Flask)
```

---

## Components

### 1. Scanner (`scanner.py`)
- Calls Marketcheck API with vehicle/location/price/mileage params
- Runs Playwright for Facebook Marketplace and Craigslist
- Returns normalized list of listings: `{id, title, price, miles, distance, city, state, source, url, score}`

### 2. Deduplicator (`db.py`)
- SQLite database storing seen listing IDs per search profile
- Filters out previously-seen listings
- Persists across runs

### 3. Email Alert (`email_alert.py`)
- Gmail SMTP via app password
- Only sends if there are new matches
- Groups listings by score tier (Ideal → Good → Ok)
- Includes direct link, price, mileage, distance, source

### 4. Dashboard (`app.py`)
- Flask web app (local)
- Shows search profile, match counts, color-coded listing cards
- "Scan Now" button triggers immediate scan
- Next scan countdown
- Listings stored in `results.json`, refreshed each scan

### 5. Scheduler (`scheduler.py`)
- APScheduler running in background thread
- Configurable interval (default: 2 hours)
- Triggers scanner → deduplicator → email alert → dashboard refresh

### 6. Config (`config.py` + `.env`)
- Search profiles: vehicle, year, max_price, max_miles, radius_miles, zip_code
- Gmail credentials (app password via `.env`)
- Marketcheck API key (via `.env`)
- Scan interval

---

## Email Format

Subject: `[CarFinder] 3 new Highlander matches found`

Body:
- Summary line: "3 new matches since last scan"
- Grouped by tier: ⭐ Ideal, ✓ Good, ~ Ok
- Each listing: title, price, mileage, distance, city, source, link

---

## Dashboard

Single-page Flask app:
- Search profile card (vehicle, max price, max miles, radius)
- Stats: total matches found, new since last alert
- Listing cards color-coded by tier
- Next scan countdown + "Scan Now" button
- No login required (local use)

---

## Multi-User Path (Future)

The search profile is a data structure from day one. Future expansion:
- Multiple profiles in SQLite
- Simple web form to add/edit a profile
- Per-profile email and scan interval

---

## Tech Stack

- **Python 3.11+**
- **Flask** — dashboard web server
- **APScheduler** — background scheduler
- **Playwright** — headless scraping (FB, Craigslist)
- **Requests** — Marketcheck API calls
- **SQLite** — deduplication store
- **smtplib** — Gmail SMTP email

---

## Out of Scope (v1)

- User authentication
- Multiple simultaneous user profiles via UI
- SMS/push notifications
- Price history tracking
- Mobile app
