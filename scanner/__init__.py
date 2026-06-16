# scanner/__init__.py
import statistics
from scanner.marketcheck import fetch_marketcheck_listings
from scanner.craigslist import fetch_craigslist_listings
from scanner.ebay import fetch_ebay_listings
from scorer import score_listing


def compute_market_values(listings: list[dict]) -> list[dict]:
    """Set market = median price of all listings in this scan."""
    prices = [l["price"] for l in listings if l.get("price")]
    if not prices:
        return listings
    median = statistics.median(prices)
    return [{**l, "market": int(median)} for l in listings]


def run_scan(search: dict) -> list[dict]:
    """Run a full scan across all sources. Returns scored, deduplicated listings."""
    mc_listings = fetch_marketcheck_listings(search)
    eb_listings = fetch_ebay_listings(search)
    cl_listings = fetch_craigslist_listings(search)

    # Merge and deduplicate by listing ID (first source wins)
    seen_ids: set[str] = set()
    all_listings: list[dict] = []
    for listing in mc_listings + eb_listings + cl_listings:
        lid = listing.get("id", "")
        if lid and lid not in seen_ids:
            seen_ids.add(lid)
            all_listings.append(listing)

    all_listings = compute_market_values(all_listings)

    scored = []
    for listing in all_listings:
        tier = score_listing(listing, search)
        if tier:
            scored.append({**listing, "tier": tier})
    return scored
