# scanner/playwright_scraper.py
import re
from playwright.sync_api import sync_playwright
from config import SEARCH

def fetch_playwright_listings() -> list[dict]:
    try:
        results = []
        results += _scrape_craigslist()
        return results
    except Exception as e:
        print(f"[playwright] scraper error (skipping): {e}")
        return []

def _scrape_craigslist() -> list[dict]:
    markets = [
        ("fayetteville", "nwar"),
        ("tulsa", "tulsa"),
        ("oklahoma", "oklahoma"),
        ("springfield", "springfield"),
        ("little rock", "littlerock"),
    ]
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for city, subdomain in markets:
            try:
                url = (
                    f"https://{subdomain}.craigslist.org/search/cta"
                    f"?query=2016+toyota+highlander"
                    f"&max_price={SEARCH['max_price']}"
                    f"&auto_miles_max={SEARCH['max_miles']}"
                    f"&sort=date"
                )
                page.goto(url, timeout=15000)
                page.wait_for_selector(".result-row", timeout=8000)
                items = page.query_selector_all(".result-row")
                for item in items[:20]:
                    try:
                        title_el = item.query_selector(".result-title")
                        price_el = item.query_selector(".result-price")
                        if not title_el or not price_el:
                            continue
                        title = title_el.inner_text().strip()
                        price_text = price_el.inner_text().strip()
                        price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
                        link = title_el.get_attribute("href") or ""
                        listing_id = f"cl_{link.split('/')[-1].replace('.html', '')}"
                        results.append({
                            "id": listing_id,
                            "title": title,
                            "price": price,
                            "miles": 0,
                            "city": city,
                            "state": "",
                            "distance": 0,
                            "source": "craigslist",
                            "url": link,
                        })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[craigslist] {subdomain} failed: {e}")
                continue
        browser.close()
    return results
