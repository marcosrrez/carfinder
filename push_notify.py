# push_notify.py
import os
import json
from pywebpush import webpush, WebPushException

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:alerts@carfinder.app"}

def send_push(subscription: dict, title: str, body: str, url: str = "/") -> bool:
    """Send a Web Push notification to one subscription. Returns True on success."""
    if not VAPID_PRIVATE_KEY:
        print("[push] VAPID_PRIVATE_KEY not set — skipping push")
        return False
    payload = json.dumps({"title": title, "body": body, "url": url})
    try:
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": {
                    "p256dh": subscription["p256dh"],
                    "auth": subscription["auth"],
                },
            },
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )
        return True
    except WebPushException as e:
        print(f"[push] Failed: {e}")
        return False

def send_push_to_user(db, user_id: str, title: str, body: str, url: str = "/") -> None:
    """Send push to all subscriptions for a user."""
    subs = db.get_push_subscriptions(user_id)
    for sub in subs:
        ok = send_push(sub, title, body, url)
        if not ok and "410" in str(sub.get("endpoint", "")):
            # Subscription expired — clean up
            db.delete_push_subscription(user_id, sub["endpoint"])
