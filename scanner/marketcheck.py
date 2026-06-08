# scanner/marketcheck.py
import hashlib
import time
import requests
from config import MARKETCHECK_API_KEY

BASE_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

# In-memory query cache: hash -> (raw_items, timestamp)
# Shared across searches with identical query params — one API call serves many users.
_cache: dict[str, tuple[list, float]] = {}
CACHE_TTL = 900  # 15 minutes


def _query_key(search: dict) -> str:
    """Stable hash of the fields that determine what Marketcheck returns."""
    parts = [
        str(search.get("make", "")).lower(),
        str(search.get("model", "")).lower(),
        str(search.get("year", "")),
        str(search.get("max_price", "")),
        str(search.get("max_miles", "")),
        str(search.get("zip", "")),
        str(search.get("radius_miles") or search.get("radius") or 100),
        str(search.get("trims", "")).lower(),
        str(search.get("drivetrain", "Any")).lower(),
    ]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _fetch_raw(search: dict, zip_code: str) -> list[dict]:
    """Hit Marketcheck and return raw listing dicts. No caching here."""
    # Plan limit: max 100 miles. Clamp regardless of what the search stores.
    radius = min(100, int(search.get("radius_miles") or search.get("radius") or 100))
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
    trims_str = search.get("trims", "")
    if trims_str:
        params["trim"] = trims_str
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


def fetch_marketcheck_count(search: dict) -> int:
    """Lightweight count-only check. Returns -1 on error."""
    zip_code = str(search.get("zip", "")).strip()
    if not zip_code:
        return -1
    radius = min(100, int(search.get("radius_miles") or search.get("radius") or 100))
    params = {
        "api_key": MARKETCHECK_API_KEY,
        "year": search["year"],
        "make": search["make"],
        "model": search["model"],
        "price_max": search["max_price"],
        "miles_max": search["max_miles"],
        "zip": zip_code,
        "radius": radius,
    }
    trims_str = search.get("trims", "")
    if trims_str:
        params["trim"] = trims_str
    drivetrain = search.get("drivetrain", "Any")
    if drivetrain and drivetrain != "Any":
        params["drivetrain"] = drivetrain
    try:
        resp = requests.get(
            "https://mc-api.marketcheck.com/v2/count/car/active",
            params=params, timeout=10
        )
        resp.raise_for_status()
        return int(resp.json().get("count", 0))
    except Exception as e:
        print(f"[marketcheck] count check error: {e}")
        return -1


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
        "market": None,
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


def clear_cache() -> None:
    """Clear the query cache — used in tests to prevent cross-test pollution."""
    _cache.clear()


def fetch_marketcheck_listings(search: dict) -> list[dict]:
    """Fetch listings using the search's zip and radius.

    Results are cached for CACHE_TTL seconds keyed on query params —
    multiple searches for the same make/model/area share one API call.
    """
    zip_code = str(search.get("zip", "")).strip()
    if not zip_code:
        print(f"[marketcheck] No zip for search {search['id']} — skipping")
        return []

    key = _query_key(search)
    now = time.time()
    cached_items, cached_at = _cache.get(key, (None, 0))

    if cached_items is not None and (now - cached_at) < CACHE_TTL:
        print(f"[marketcheck] Cache hit for {search['make']} {search['model']} "
              f"near {zip_code} (age {int(now - cached_at)}s) — {len(cached_items)} items")
        raw_items = cached_items
    else:
        raw_items = _fetch_raw(search, zip_code)
        _cache[key] = (raw_items, now)
        print(f"[marketcheck] Fetched {len(raw_items)} listings for "
              f"{search['make']} {search['model']} near {zip_code}")

    seen_ids: set[str] = set()
    results = []
    for item in raw_items:
        normalized = _normalize(item, search["id"])
        if normalized["id"] not in seen_ids:
            seen_ids.add(normalized["id"])
            results.append(normalized)
    return results
