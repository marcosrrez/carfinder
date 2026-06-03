# scheduler.py
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import run_scan
from db import ListingDB
from email_alert import send_alert
from app import app, save_results
from config import SEARCH

db = ListingDB()
_next_scan_time = None

def trigger_scan():
    global _next_scan_time
    print(f"[scheduler] Running scan at {datetime.now().strftime('%H:%M:%S')}")
    try:
        all_listings = run_scan()
        new_listings = db.filter_new(all_listings)
        print(f"[scheduler] Found {len(all_listings)} total, {len(new_listings)} new")
        send_alert(new_listings)
        interval = SEARCH["scan_interval_hours"]
        _next_scan_time = datetime.now() + timedelta(hours=interval)
        save_results(all_listings, len(new_listings), _next_scan_time.isoformat())
    except Exception as e:
        print(f"[scheduler] Scan error: {e}")

def start():
    interval_hours = SEARCH["scan_interval_hours"]
    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger_scan, "interval", hours=interval_hours, id="scan")
    scheduler.start()
    print(f"[scheduler] Scan scheduled every {interval_hours}h. Running first scan now...")
    threading.Thread(target=trigger_scan, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)

if __name__ == "__main__":
    start()
