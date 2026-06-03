import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise ValueError(f"Missing required env var: {key}. Check your .env file.")
    return val

MARKETCHECK_API_KEY = _require("MARKETCHECK_API_KEY")
GMAIL_USER = _require("GMAIL_USER")
GMAIL_APP_PASSWORD = _require("GMAIL_APP_PASSWORD")
ALERT_EMAIL = _require("ALERT_EMAIL")

SEARCH = {
    "make": "Toyota",
    "model": "Highlander",
    "year": 2016,
    "max_price": 20600,
    "max_miles": 130000,
    "zip": "72761",       # Siloam Springs AR
    "radius_miles": 300,
    "scan_interval_hours": 2,
}

IDEAL = {"max_price": 18500, "max_miles": 90000}
GOOD  = {"max_price": 20600, "max_miles": 80000}
