# scanner/craigslist.py
"""Craigslist car listings scraper.

Dynamically selects Craigslist metro areas within the search radius using
scanner.markets. Handles both the old (.result-row) and new (li.cl-search-result)
Craigslist HTML layouts. One browser instance is shared across all markets.
"""
import re
import time
from playwright.sync_api import sync_playwright
from scanner.markets import craigslist_markets_near

_PAGE_TIMEOUT = 12000
_SELECTOR_TIMEOUT = 6000


def _parse_miles_from_title(title: str) -> int | None:
    """Extract mileage from a listing title string.

    Handles:
      '89k miles'  → 89000
      '89K mi'     → 89000
      '102,000 miles' → 102000
      '102000 mi'  → 102000
    Returns None if no mileage pattern found.
    """
    m = re.search(r'(\d[\d,]*)([kK])?\s*(?:miles?|mi)\b', title, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        val = int(raw)
        if m.group(2):  # k suffix
            val *= 1000
        return val
    except ValueError:
        return None


def _build_url(subdomain: str, search: dict) -> str:
    make = search["make"].replace(" ", "+")
    model = search["model"].replace(" ", "+")
    year = search["year"]
    max_price = search["max_price"]
    max_miles = search["max_miles"]
    return (
        f"https://{subdomain}.craigslist.org/search/cta"
        f"?auto_make_model={make}+{model}"
        f"&auto_year1={year}&auto_year2={year}"
        f"&max_price={max_price}&auto_miles_max={max_miles}"
        f"&sort=date&srchType=T"
    )


def _scrape_page_new_layout(page, subdomain: str, search: dict) -> list[dict]:
    """Parse Craigslist's current (2024+) layout: li.cl-search-result elements."""
    items = page.query_selector_all("li.cl-search-result")
    results = []
    for item in items[:25]:
        try:
            anchor = item.query_selector("a.cl-app-anchor")
            if not anchor:
                continue
            title_el = anchor.query_selector(".label") or anchor.query_selector("span")
            price_el = item.query_selector(".priceinfo") or item.query_selector(".price")
            title = (title_el.inner_text().strip() if title_el else anchor.inner_text().strip())
            if not title:
                continue
            price_text = price_el.inner_text().strip() if price_el else ""
            price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
            link = anchor.get_attribute("href") or ""
            if link and not link.startswith("http"):
                link = f"https://{subdomain}.craigslist.org{link}"
            pid = item.get_attribute("data-pid") or link.split("/")[-1].replace(".html", "")
            listing_id = f"cl_{pid}"
            miles = _parse_miles_from_title(title)
            results.append(_make_listing(listing_id, search, title, price, miles, link, subdomain))
        except Exception:
            continue
    return results


def _scrape_page_old_layout(page, subdomain: str, search: dict) -> list[dict]:
    """Parse Craigslist's old layout: .result-row elements."""
    items = page.query_selector_all(".result-row")
    results = []
    for item in items[:25]:
        try:
            title_el = item.query_selector(".result-title")
            price_el = item.query_selector(".result-price")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            price_text = price_el.inner_text().strip() if price_el else ""
            price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
            link = title_el.get_attribute("href") or ""
            pid = link.split("/")[-1].replace(".html", "")
            listing_id = f"cl_{pid}"
            miles = _parse_miles_from_title(title)
            results.append(_make_listing(listing_id, search, title, price, miles, link, subdomain))
        except Exception:
            continue
    return results


def _make_listing(listing_id: str, search: dict, title: str,
                  price: int, miles: int | None, url: str, subdomain: str) -> dict:
    return {
        "id": listing_id,
        "search_id": search["id"],
        "title": title,
        "price": price,
        "miles": miles or 0,
        "city": subdomain,
        "state": "",
        "distance": 0,
        "source": "craigslist",
        "url": url,
        "market": None,
        "drivetrain": "",
        "exterior": "",
        "interior": "",
        "owners": None,
        "accidents": None,
        "days_listed": None,
        "photos": 0,
        "seller_type": "Private",
        "seller_name": "Private seller",
        "seller_rating": None,
        "vin": "",
        "drop_amount": None,
        "drop_when": None,
        "is_new": 1,
    }


def fetch_craigslist_listings(search: dict) -> list[dict]:
    """Scrape Craigslist markets within the search's ZIP+radius.

    Returns empty list on any browser error (fail-safe).
    Deduplicates by listing ID across markets.
    """
    zip_code = str(search.get("zip", "")).strip()
    radius = int(search.get("radius_miles") or search.get("radius") or 100)
    markets = craigslist_markets_near(zip_code, radius)

    if not markets:
        print(f"[craigslist] No markets found for ZIP {zip_code} radius {radius}mi")
        return []

    print(f"[craigslist] {len(markets)} markets in range: {[m[1] for m in markets]}")

    results: list[dict] = []
    seen_ids: set[str] = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            for city_label, subdomain in markets:
                url = _build_url(subdomain, search)
                try:
                    page.goto(url, timeout=_PAGE_TIMEOUT, wait_until="domcontentloaded")
                    new_items = page.query_selector_all("li.cl-search-result")
                    if new_items:
                        listings = _scrape_page_new_layout(page, subdomain, search)
                    else:
                        page.wait_for_selector(".result-row", timeout=_SELECTOR_TIMEOUT)
                        listings = _scrape_page_old_layout(page, subdomain, search)

                    fresh = [l for l in listings if l["id"] not in seen_ids]
                    for l in fresh:
                        seen_ids.add(l["id"])
                    results.extend(fresh)
                    print(f"[craigslist] {subdomain}: {len(fresh)} listings")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[craigslist] {subdomain} failed: {e}")
                    continue

            browser.close()
    except Exception as e:
        print(f"[craigslist] Browser error (skipping): {e}")
        return []

    return results
