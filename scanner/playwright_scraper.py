# scanner/playwright_scraper.py
"""Thin shim — delegates to scanner.craigslist.

Kept for backwards compatibility with existing imports and tests.
"""
from scanner.craigslist import fetch_craigslist_listings


def fetch_playwright_listings(search: dict) -> list[dict]:
    return fetch_craigslist_listings(search)
