# scanner/playwright_scraper.py
import re
from playwright.sync_api import sync_playwright

def fetch_playwright_listings(search: dict) -> list[dict]:
    try:
        return _scrape_craigslist(search)
    except Exception as e:
        print(f"[playwright] scraper error (skipping): {e}")
        return []

def _scrape_craigslist(search: dict) -> list[dict]:
    markets = [
        ("fayetteville", "nwar"), ("tulsa", "tulsa"),
        ("oklahoma", "oklahoma"), ("springfield", "springfield"),
        ("little rock", "littlerock"),
    ]
    results = []
    query = f"{search['year']}+{search['make']}+{search['model']}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for city, subdomain in markets:
            try:
                url = (
                    f"https://{subdomain}.craigslist.org/search/cta"
                    f"?query={query}&max_price={search['max_price']}"
                    f"&auto_miles_max={search['max_miles']}&sort=date"
                )
                page.goto(url, timeout=15000)
                page.wait_for_selector(".result-row", timeout=8000)
                for item in page.query_selector_all(".result-row")[:20]:
                    try:
                        title_el = item.query_selector(".result-title")
                        price_el = item.query_selector(".result-price")
                        if not title_el or not price_el:
                            continue
                        title = title_el.inner_text().strip()
                        price_text = price_el.inner_text().strip()
                        price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
                        link = title_el.get_attribute("href") or ""
                        listing_id = f"cl_{link.split('/')[-1].replace('.html','')}"
                        results.append({
                            "id": listing_id, "search_id": search["id"],
                            "title": title, "price": price, "miles": 0,
                            "city": city, "state": "", "distance": 0,
                            "source": "craigslist", "url": link,
                            "market": None, "drivetrain": "", "exterior": "",
                            "interior": "", "owners": None, "accidents": None,
                            "days_listed": None, "photos": 0,
                            "seller_type": "Private", "seller_name": "Private seller",
                            "seller_rating": None, "vin": "",
                            "drop_amount": None, "drop_when": None, "is_new": 1,
                        })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[craigslist] {subdomain} failed: {e}")
                continue
        browser.close()
    return results
