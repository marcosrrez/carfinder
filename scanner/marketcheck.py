# scanner/marketcheck.py
import requests
from config import MARKETCHECK_API_KEY, SEARCH

BASE_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

# Strategic zip codes covering ~300mi radius from Siloam Springs AR (72761).
# Free tier caps radius at 100mi, so we fan out from multiple centers.
SEARCH_ZIPS = [
    "72761",  # Siloam Springs AR (home base)
    "74101",  # Tulsa OK (~90mi)
    "64801",  # Joplin MO (~80mi)
    "65801",  # Springfield MO (~120mi)
    "72901",  # Fort Smith AR (~50mi)
    "73101",  # Oklahoma City OK (~180mi)
    "72201",  # Little Rock AR (~200mi)
    "64108",  # Kansas City MO (~280mi)
]

def _fetch_zip(zip_code: str) -> list[dict]:
    params = {
        "api_key": MARKETCHECK_API_KEY,
        "year": SEARCH["year"],
        "make": SEARCH["make"],
        "model": SEARCH["model"],
        "price_max": SEARCH["max_price"],
        "miles_max": SEARCH["max_miles"],
        "zip": zip_code,
        "radius": 100,
        "rows": 100,
        "start": 0,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[marketcheck] {zip_code} error (skipping): {e}")
        return []

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

def fetch_marketcheck_listings() -> list[dict]:
    seen_ids = set()
    all_results = []
    for zip_code in SEARCH_ZIPS:
        for listing in _fetch_zip(zip_code):
            if listing["id"] not in seen_ids:
                seen_ids.add(listing["id"])
                all_results.append(listing)
    print(f"[marketcheck] {len(all_results)} unique listings across {len(SEARCH_ZIPS)} zones")
    return all_results
