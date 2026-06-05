# scheduler.py
import os
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, get_db
from scanner import run_scan
from email_alert import send_alert

_status = {"scanning": False, "last_scan": None, "next_scan": None}
_status_lock = threading.Lock()

def get_status() -> dict:
    with _status_lock:
        return dict(_status)

def _set_status(**kwargs):
    with _status_lock:
        _status.update(kwargs)

def trigger_scan_for_search(search: dict) -> None:
    """Scan one search profile, persist results, send alert for new matches."""
    db = get_db()
    print(f"[scheduler] Scanning: {search['make']} {search['model']} (id={search['id']})")
    _set_status(scanning=True)
    try:
        listings = run_scan(search)
        new_listings = []
        for listing in listings:
            existing = db.conn.execute(
                "SELECT id, is_new FROM listings WHERE id=? AND search_id=?",
                (listing["id"], search["id"])
            ).fetchone()
            listing["is_new"] = 0 if existing else 1
            db.upsert_listing(listing)
            if not existing:
                new_listings.append(listing)

        print(f"[scheduler] {len(listings)} total, {len(new_listings)} new for search {search['id']}")
        if new_listings:
            send_alert(search, new_listings)
    except Exception as e:
        print(f"[scheduler] Error scanning {search['id']}: {e}")
    finally:
        _set_status(
            scanning=False,
            last_scan=datetime.now().isoformat(),
        )

def trigger_scan_for_user(user_id: str) -> None:
    """Scan all active searches for a given user."""
    db = get_db()
    searches = db.list_searches(user_id)
    for search in searches:
        trigger_scan_for_search(search)

def _run_all_active_searches() -> None:
    """Scheduled job: scan every active search across all users."""
    db = get_db()
    searches = db.list_all_active_searches()
    print(f"[scheduler] Scheduled scan — {len(searches)} active searches")
    for search in searches:
        trigger_scan_for_search(search)

def start():
    flask_app = create_app()
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_all_active_searches, "interval", hours=2, id="scan_all")
    scheduler.start()
    print("[scheduler] APScheduler started. Running initial scan...")
    threading.Thread(target=_run_all_active_searches, daemon=True).start()
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start()
