# scanner/ebay.py
"""eBay Motors Finding API client.

Uses the public eBay Finding API (App ID only, no OAuth).
Category 6001 = Cars & Trucks.
Results are cached for 15 minutes (same pattern as Marketcheck).

Sign up at https://developer.ebay.com/join/ to get a free App ID.
"""
import hashlib
import time
import requests
from scanner.craigslist import _parse_miles_from_title

try:
    from config import EBAY_APP_ID
except ImportError:
    EBAY_APP_ID = None

FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
CACHE_TTL = 900  # 15 minutes
_cache: dict[str, tuple[list, float]] = {}


def clear_cache() -> None:
    _cache.clear()


def _query_key(search: dict) -> str:
    parts = [
        str(search.get("make", "")).lower(),
        str(search.get("model", "")).lower(),
        str(search.get("year", "")),
        str(search.get("max_price", "")),
        str(search.get("max_miles", "")),
        str(search.get("zip", "")),
        str(search.get("radius_miles") or search.get("radius") or 100),
    ]
    return "eb_" + hashlib.md5("|".join(parts).encode()).hexdigest()


def _normalize(item: dict, search_id: str) -> dict:
    """Convert a raw eBay Finding API item dict to CarFinder listing format."""
    item_id = (item.get("itemId") or [""])[0]
    title = (item.get("title") or [""])[0]
    price_raw = (
        ((item.get("sellingStatus") or [{}])[0]
         .get("currentPrice") or [{}])[0]
        .get("__value__", "0")
    )
    url = (
        ((item.get("listingInfo") or [{}])[0]
         .get("viewItemURL") or [""])[0]
    )
    location_str = (item.get("location") or [""])[0]
    parts = [p.strip() for p in location_str.split(",")]
    city = parts[0] if parts else ""
    state = parts[1] if len(parts) > 1 else ""

    photos_raw = item.get("pictureURLSuperSize") or item.get("galleryPlusPictureURL") or []
    photos = len(photos_raw) if isinstance(photos_raw, list) else (1 if photos_raw else 0)

    miles = _parse_miles_from_title(title) or 0

    try:
        price = int(float(price_raw))
    except (ValueError, TypeError):
        price = 0

    return {
        "id": f"eb_{item_id}",
        "search_id": search_id,
        "title": title,
        "price": price,
        "miles": miles,
        "city": city,
        "state": state,
        "distance": 0,
        "source": "ebay",
        "url": url,
        "market": None,
        "drivetrain": "",
        "exterior": "",
        "interior": "",
        "owners": None,
        "accidents": None,
        "days_listed": None,
        "photos": photos,
        "seller_type": "Private",
        "seller_name": "eBay seller",
        "seller_rating": None,
        "vin": "",
        "drop_amount": None,
        "drop_when": None,
        "is_new": 1,
    }


def fetch_ebay_listings(search: dict) -> list[dict]:
    """Fetch used car listings from eBay Motors Finding API.

    Returns [] if EBAY_APP_ID is not configured.
    Results cached for 15 minutes per unique query.
    """
    if not EBAY_APP_ID:
        print("[ebay] EBAY_APP_ID not set — skipping eBay source")
        return []

    key = _query_key(search)
    now = time.time()
    cached_items, cached_at = _cache.get(key, (None, 0))
    if cached_items is not None and (now - cached_at) < CACHE_TTL:
        print(f"[ebay] Cache hit — {len(cached_items)} items (age {int(now - cached_at)}s)")
        raw_items = cached_items
    else:
        raw_items = _fetch_raw(search)
        _cache[key] = (raw_items, now)

    seen_ids: set[str] = set()
    results = []
    for item in raw_items:
        normalized = _normalize(item, search["id"])
        # Only filter by miles when we actually parsed a mileage from the title
        # (miles == 0 means "unknown", not "zero miles driven")
        if normalized["miles"] and normalized["miles"] > search.get("max_miles", 999999):
            continue
        if normalized["id"] not in seen_ids:
            seen_ids.add(normalized["id"])
            results.append(normalized)
    print(f"[ebay] {len(results)} listings for {search['make']} {search['model']}")
    return results


def _fetch_raw(search: dict) -> list[dict]:
    """Call eBay Finding API and return raw item dicts."""
    keywords = f"{search['year']} {search['make']} {search['model']}"
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "categoryId": "6001",
        "keywords": keywords,
        "itemFilter(0).name": "MaxPrice",
        "itemFilter(0).value": str(search["max_price"]),
        "itemFilter(0).paramName": "Currency",
        "itemFilter(0).paramValue": "USD",
        "itemFilter(1).name": "Condition",
        "itemFilter(1).value": "3000",
        "itemFilter(2).name": "ListingType",
        "itemFilter(2).value": "FixedPrice",
        "itemFilter(2).value(1)": "Auction",
        "buyerPostalCode": str(search.get("zip", "")),
        "sortOrder": "Distance",
        "paginationInput.entriesPerPage": "100",
        "outputSelector(0)": "PictureURLSuperSize",
        "outputSelector(1)": "GalleryInfo",
    }
    try:
        resp = requests.get(FINDING_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        response_wrapper = data.get("findItemsAdvancedResponse", [{}])[0]
        search_result = response_wrapper.get("searchResult", [{}])[0]
        items = search_result.get("item", [])
        print(f"[ebay] API returned {len(items)} raw items")
        return items
    except Exception as e:
        print(f"[ebay] API error: {e}")
        return []
