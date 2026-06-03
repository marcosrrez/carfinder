from scanner.marketcheck import fetch_marketcheck_listings
from scanner.playwright_scraper import fetch_playwright_listings
from scorer import score_listing

def run_scan() -> list[dict]:
    listings = fetch_marketcheck_listings() + fetch_playwright_listings()
    scored = []
    for listing in listings:
        tier = score_listing(listing)
        if tier:
            scored.append({**listing, "score": tier})
    return scored
