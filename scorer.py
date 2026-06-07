# scorer.py

def score_listing(listing: dict, search: dict) -> str | None:
    price = listing["price"]
    miles = listing["miles"]
    max_price = search["max_price"]
    max_miles = search["max_miles"]
    ideal_price = search["ideal_price"]
    ideal_miles = search["ideal_miles"]

    if price > max_price or miles > max_miles:
        return None

    if price <= ideal_price and miles <= ideal_miles:
        return "ideal"

    near_price = price > max_price * 0.92
    near_miles = miles > max_miles * 0.92
    if near_price or near_miles:
        return "ok"

    # If miles exceeded ideal threshold, it's "ok"
    if miles > ideal_miles:
        return "ok"

    # Otherwise (price > ideal but miles <= ideal, and not near caps): "good"
    return "good"


def deal_for(listing: dict) -> dict:
    market = listing.get("market") or listing["price"]
    delta = listing["price"] - market
    if delta <= -1200:
        return {"key": "great", "label": "Great deal", "delta": delta}
    if delta <= -300:
        return {"key": "good", "label": "Good price", "delta": delta}
    if delta <= 600:
        return {"key": "fair", "label": "Fair price", "delta": delta}
    return {"key": "high", "label": "Above market", "delta": delta}


def trim_matches(listing: dict, search: dict) -> bool:
    """True if the listing's trim matches any of the search's selected trims."""
    trims_str = search.get("trims", "")
    if not trims_str:
        return False
    selected = [t.strip().lower() for t in trims_str.split(",") if t.strip()]
    if not selected:
        return False
    # Check trim field first, fall back to title
    text = (listing.get("trim") or listing.get("title") or "").lower()
    return any(t in text for t in selected)
