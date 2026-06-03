from config import SEARCH, IDEAL, GOOD

def score_listing(listing: dict) -> str | None:
    price = listing["price"]
    miles = listing["miles"]

    if price > SEARCH["max_price"] or miles > SEARCH["max_miles"]:
        return None

    if price <= IDEAL["max_price"] and miles <= IDEAL["max_miles"]:
        return "ideal"

    if price <= GOOD["max_price"] and miles <= GOOD["max_miles"]:
        return "good"

    return "ok"
