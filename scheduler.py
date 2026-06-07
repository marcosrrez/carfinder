# scheduler.py
import os
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, get_db
from scanner import run_scan
from scanner.marketcheck import fetch_marketcheck_count
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
            drop_info = db.upsert_listing(listing)
            if drop_info["price_dropped"] and drop_info["saved_by"]:
                from email_alert import send_price_drop_alert
                print(f"[scanner] Price drop on saved listing {listing['id']} — ${drop_info['drop_amount']:,}")
                send_price_drop_alert(search, listing, drop_info["drop_amount"])
        count_new = sum(1 for l in listings if l.get("is_new"))
        print(f"[scanner] {len(listings)} total, {count_new} new for search {search['id']}")
        new_listings = [l for l in listings if l.get("is_new")]
        # Send push notifications for new listings
        if new_listings:
            from push_notify import send_push_to_user
            user_id = search.get("user_id")
            if user_id:
                best = min(new_listings, key=lambda l: l.get("price", 999999))
                count = len(new_listings)
                title = f"{count} new {search['make']} {search['model']} match{'es' if count > 1 else ''}"
                price = f"${best['price']:,}"
                miles = f"{best['miles']:,} mi"
                body = f"Best: {price} · {miles}"
                market = best.get("market")
                if market and best["price"] < market:
                    delta = market - best["price"]
                    body += f" — ${delta:,} below market"
                send_push_to_user(db, user_id, title, body)
        now = datetime.now().isoformat()
        db.update_scan_timestamps(search["id"], last_scanned_at=now)
        db.update_scan_timestamps(search["id"], last_listing_count=len(listings))
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

def _scan_interval_minutes(search: dict, db) -> int:
    """Return how often (in minutes) this search should be scanned.

    Tiers:
      - New search (< 24h old): 20 min — user is actively hunting
      - Has listings found recently (< 7 days): 20 min — hot search
      - No matches in 7–30 days: 120 min — cooling off
      - No matches ever or > 30 days stale: 360 min — hibernating
    """
    now = datetime.now()
    created_at_str = search.get("created_at") or ""
    try:
        age_hours = (now - datetime.fromisoformat(created_at_str)).total_seconds() / 3600
    except Exception:
        age_hours = 999

    if age_hours < 24:
        return 20  # brand-new search, always hot

    # Check when we last found a new listing
    row = db.conn.execute(
        "SELECT MAX(first_seen) as latest FROM listings WHERE search_id = ?",
        (search["id"],)
    ).fetchone()
    latest_str = row["latest"] if row else None

    if not latest_str:
        return 360  # never found anything — hibernate

    try:
        days_since_match = (now - datetime.fromisoformat(latest_str)).days
    except Exception:
        days_since_match = 999

    if days_since_match < 7:
        return 20   # actively finding things
    if days_since_match < 30:
        return 120  # quieter but still relevant
    return 120  # stale but never wait more than 2h


def _should_scan_now(search: dict, interval_minutes: int) -> bool:
    """True if enough time has passed since the last scan for this search."""
    last_str = search.get("last_scanned_at")
    if not last_str:
        return True
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(last_str)).total_seconds() / 60
        return elapsed >= interval_minutes
    except Exception:
        return True


def _run_all_scans() -> None:
    """Scheduled job: scan active searches with tiered cadence + count-check wake-up."""
    db = get_db()
    searches = db.list_all_active_searches()
    full_scan = []
    count_woken = []
    skipped = []

    for search in searches:
        interval = _scan_interval_minutes(search, db)
        if _should_scan_now(search, interval):
            full_scan.append(search)
        elif interval >= 120:
            # Hibernating/cooling — do a cheap count check to detect new inventory
            current_count = fetch_marketcheck_count(search)
            stored_count = search.get("last_listing_count") or 0
            if current_count >= 0 and current_count != stored_count:
                print(f"[scanner] Count changed for {search['id']}: "
                      f"{stored_count} → {current_count} — waking up")
                count_woken.append(search)
            else:
                skipped.append(search["id"])
        else:
            skipped.append(search["id"])

    print(f"[scanner] Tick — {len(full_scan)} full scans, "
          f"{len(count_woken)} count-woken, {len(skipped)} skipped")

    for search in full_scan + count_woken:
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

def _run_quiet_alerts() -> None:
    """Send a weekly nudge email for searches that have been quiet 7+ days."""
    from email_alert import send_quiet_alert
    db = get_db()
    searches = db.list_all_active_searches()
    now = datetime.now()
    for search in searches:
        # Only alert searches with an email address
        if not search.get("alert_emails"):
            continue
        # Check last match date
        row = db.conn.execute(
            "SELECT MAX(first_seen) as latest FROM listings WHERE search_id = ?",
            (search["id"],)
        ).fetchone()
        latest_str = row["latest"] if row else None
        if not latest_str:
            # Never found anything — use created_at
            latest_str = search.get("created_at", now.isoformat())
        try:
            days_quiet = (now - datetime.fromisoformat(latest_str)).days
        except Exception:
            continue
        if days_quiet < 7:
            continue  # Not quiet enough
        # Only send once per week — use last_alerted_at as proxy
        last_alerted = search.get("last_alerted_at")
        if last_alerted:
            try:
                days_since_alert = (now - datetime.fromisoformat(last_alerted)).days
                if days_since_alert < 7:
                    continue
            except Exception:
                pass
        print(f"[quiet] Sending quiet alert for search {search['id']} ({days_quiet} days quiet)")
        try:
            send_quiet_alert(search, days_quiet)
        except Exception as e:
            print(f"[quiet] Failed: {e}")


def _run_weekly_digest() -> None:
    """Send weekly summary email to all users with active searches."""
    from email_alert import send_digest
    from datetime import timedelta
    db = get_db()
    searches = db.list_all_active_searches()
    now = datetime.now()
    one_week_ago = (now - timedelta(days=7)).isoformat()

    # Group searches by user_id
    by_user: dict[str, list] = {}
    for s in searches:
        uid = s.get("user_id", "")
        if uid:
            by_user.setdefault(uid, []).append(s)

    for user_id, user_searches in by_user.items():
        summaries = []
        for search in user_searches:
            listings = db.get_listings(search["id"])
            new_this_week = [l for l in listings if l.get("first_seen", "") >= one_week_ago]

            # Best listing by price delta (most below market)
            with_market = [l for l in listings if l.get("market") and l.get("price")]
            best = None
            best_delta = None
            if with_market:
                best = min(with_market, key=lambda l: l["price"] - l["market"])
                best_delta = best["price"] - best["market"]

            # Days quiet
            latest_str = max((l.get("first_seen", "") for l in listings), default=None)
            days_quiet = 0
            if latest_str:
                try:
                    days_quiet = (now - datetime.fromisoformat(latest_str)).days
                except Exception:
                    pass
            else:
                days_quiet = 999

            summaries.append({
                "search": search,
                "total_listings": len(listings),
                "new_this_week": len(new_this_week),
                "best_listing": best,
                "best_delta": best_delta,
                "days_quiet": days_quiet,
            })

        print(f"[digest] Sending weekly digest to user {user_id} ({len(summaries)} searches)")
        try:
            send_digest(user_id, summaries)
        except Exception as e:
            print(f"[digest] Failed for user {user_id}: {e}")


def start():
    flask_app = create_app()
    scheduler = BackgroundScheduler()

    # Scan all searches every 20 minutes
    scheduler.add_job(_run_all_scans, "interval", minutes=20, id="scan_all")

    # Check who needs an alert every 5 minutes
    scheduler.add_job(_run_all_alerts, "interval", minutes=5, id="alert_all")

    # Send weekly quiet-search nudge emails once daily
    scheduler.add_job(_run_quiet_alerts, "interval", hours=24, id="quiet_alerts")

    # Weekly digest every Sunday at 9am
    scheduler.add_job(_run_weekly_digest, "cron", day_of_week="sun", hour=9, id="weekly_digest")

    scheduler.start()

    # Run initial scan immediately in background
    print("[scheduler] APScheduler started. Running initial scan...")
    threading.Thread(target=_run_all_scans, daemon=True).start()

    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    start()
