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

def _schedule_search(scheduler: BackgroundScheduler, search: dict) -> None:
    """Add or replace a scheduled job for a single search."""
    job_id = f"scan_{search['id']}"
    hours = max(1, int(search.get("interval_hours") or 2))
    scheduler.add_job(
        trigger_scan_for_search,
        "interval",
        hours=hours,
        id=job_id,
        args=[search],
        replace_existing=True,
    )
    print(f"[scheduler] Scheduled {search['make']} {search['model']} every {hours}h (job={job_id})")


def reschedule_all(scheduler: BackgroundScheduler) -> None:
    """Re-read all active searches from DB and sync scheduler jobs."""
    db = get_db()
    searches = db.list_all_active_searches()
    active_ids = {f"scan_{s['id']}" for s in searches}

    # Remove jobs for deleted/inactive searches
    for job in scheduler.get_jobs():
        if job.id.startswith("scan_") and job.id not in active_ids:
            scheduler.remove_job(job.id)
            print(f"[scheduler] Removed job {job.id}")

    # Add/update jobs for active searches
    for search in searches:
        _schedule_search(scheduler, search)


def start():
    flask_app = create_app()
    scheduler = BackgroundScheduler()

    # Sync all per-search jobs every 5 minutes (picks up new searches, interval changes)
    scheduler.add_job(
        lambda: reschedule_all(scheduler),
        "interval",
        minutes=5,
        id="reschedule_all",
    )

    scheduler.start()
    reschedule_all(scheduler)

    print("[scheduler] APScheduler started. Running initial scan...")
    threading.Thread(target=_run_all_active_searches, daemon=True).start()
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start()
