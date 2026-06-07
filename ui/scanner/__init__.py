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
