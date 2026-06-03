import os
from dotenv import load_dotenv

load_dotenv()

MARKETCHECK_API_KEY = os.environ["MARKETCHECK_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ALERT_EMAIL = os.environ["ALERT_EMAIL"]

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
