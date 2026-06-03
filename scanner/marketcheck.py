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
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[marketcheck] API error (skipping): {e}")
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
