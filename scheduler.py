# scheduler.py
import os
import threading
from datetime import datetime, timedelta
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
    """Scan one search, persist results. Does NOT send alerts."""
    db = get_db()
    print(f"[scanner] Scanning: {search['make']} {search['model']} (id={search['id']})")
    _set_status(scanning=True)
    try:
        listings = run_scan(search)
        for listing in listings:
            existing = db.conn.execute(
                "SELECT id, is_new FROM listings WHERE id=? AND search_id=?",
                (listing["id"], search["id"])
            ).fetchone()
            listing["is_new"] = 0 if existing else 1
            db.upsert_listing(listing)
        count_new = sum(1 for l in listings if l.get("is_new"))
        print(f"[scanner] {len(listings)} total, {count_new} new for search {search['id']}")
        now = datetime.now().isoformat()
        db.update_scan_timestamps(search["id"], last_scanned_at=now)
    except Exception as e:
        print(f"[scanner] Error scanning {search['id']}: {e}")
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

def _run_all_scans() -> None:
    """Scheduled job: scan every active search. No emails."""
    db = get_db()
    searches = db.list_all_active_searches()
    print(f"[scanner] Scheduled scan — {len(searches)} active searches")
    for search in searches:
        trigger_scan_for_search(search)

def _run_all_alerts() -> None:
    """Scheduled job: send alert emails for searches whose interval has elapsed."""
    db = get_db()
    searches = db.list_all_active_searches()
    now = datetime.now()
    for search in searches:
        interval_hours = max(1, int(search.get("interval_hours") or 2))
        last_alerted = search.get("last_alerted_at")
        if last_alerted:
            next_alert_due = datetime.fromisoformat(last_alerted) + timedelta(hours=interval_hours)
            if now < next_alert_due:
                continue  # Not time yet
        # Time to alert — find new listings since last alert
        listings = db.get_listings(search["id"])
        if last_alerted:
            new_listings = [
                l for l in listings
                if l.get("is_new") and l.get("first_seen") and
                   l["first_seen"] >= last_alerted
            ]
        else:
            # Cold start: only alert on listings found after search was created
            created_at = search.get("created_at", "")
            new_listings = [
                l for l in listings
                if l.get("is_new") and l.get("first_seen") and
                   l["first_seen"] >= created_at
            ]
        if new_listings:
            print(f"[alerts] Sending alert for search {search['id']} — {len(new_listings)} new listings")
            try:
                send_alert(search, new_listings)
            except Exception as e:
                print(f"[alerts] Failed to send alert for {search['id']}: {e}")
        else:
            print(f"[alerts] No new listings for search {search['id']} — skipping email")
        # Always update last_alerted_at so interval resets even if no email was sent
        db.update_scan_timestamps(search["id"], last_alerted_at=now.isoformat())

def start():
    flask_app = create_app()
    scheduler = BackgroundScheduler()

    # Scan all searches every 20 minutes
    scheduler.add_job(_run_all_scans, "interval", minutes=20, id="scan_all")

    # Check who needs an alert every 5 minutes
    scheduler.add_job(_run_all_alerts, "interval", minutes=5, id="alert_all")

    scheduler.start()

    # Run initial scan immediately in background
    print("[scheduler] APScheduler started. Running initial scan...")
    threading.Thread(target=_run_all_scans, daemon=True).start()

    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start()
