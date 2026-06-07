# scanner/marketcheck.py
import requests
from config import MARKETCHECK_API_KEY

BASE_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

def _fetch_zip(search: dict, zip_code: str) -> list[dict]:
    radius = search.get("radius_miles") or search.get("radius") or 100
    params = {
        "api_key": MARKETCHECK_API_KEY,
        "year": search["year"],
        "make": search["make"],
        "model": search["model"],
        "price_max": search["max_price"],
        "miles_max": search["max_miles"],
        "zip": zip_code,
        "radius": radius,
        "rows": 100,
        "start": 0,
        "fields": "id,heading,price,miles,dealer,dist,vdp_url,build,extra,dom,media,seller,vin,price_history",
    }
    # Trim filter — comma-separated, Marketcheck matches any (OR logic)
    trims_str = search.get("trims", "")
    if trims_str:
        params["trim"] = trims_str

    # Drivetrain filter — AND on top of trim selection
    drivetrain = search.get("drivetrain", "Any")
    if drivetrain and drivetrain != "Any":
        params["drivetrain"] = drivetrain

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
    """Fetch listings using the search's own zip and radius_miles."""
    seen_ids = set()
    results = []
    zip_code = str(search.get("zip", "")).strip()
    if not zip_code:
        print(f"[marketcheck] No zip for search {search['id']} — skipping")
        return []
    for item in _fetch_zip(search, zip_code):
        normalized = _normalize(item, search["id"])
        if normalized["id"] not in seen_ids:
            seen_ids.add(normalized["id"])
            results.append(normalized)
    print(f"[marketcheck] {len(results)} unique listings for {search['make']} {search['model']} near {zip_code}")
    return results
