# seed.py
"""One-time seed: creates the default Highlander search for user_marcos."""
from models import Database

db = Database()
existing = db.list_searches("user_marcos")
if existing:
    print("Already seeded.")
else:
    s = db.create_search({
        "user_id": "user_marcos",
        "make": "Toyota", "model": "Highlander", "trim": "",
        "year": 2016, "max_price": 20600, "ideal_price": 18500,
        "max_miles": 130000, "ideal_miles": 90000,
        "zip": "72761", "city": "Siloam Springs, AR",
        "radius_miles": 300, "interval_hours": 2,
        "alert_email": "marcosrrez@gmail.com",
    })
    print(f"Seeded search: {s['id']}")
db.close()
