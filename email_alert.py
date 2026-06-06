# email_alert.py
import resend
from config import RESEND_API_KEY, RESEND_FROM

TIER_LABELS = {"ideal": "⭐ IDEAL", "good": "✓ GOOD", "ok": "~ OK"}
TIER_ORDER = ["ideal", "good", "ok"]

def build_email_body(search: dict, listings: list[dict]) -> str:
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    grouped = {tier: [] for tier in TIER_ORDER}
    for listing in listings:
        tier = listing.get("tier", "ok")
        grouped[tier].append(listing)

    lines = [f"{len(listings)} new match(es) for your {vehicle} search.\n"]
    for tier in TIER_ORDER:
        group = grouped[tier]
        if not group:
            continue
        lines.append(f"\n{'='*40}")
        lines.append(f"{TIER_LABELS[tier]} ({len(group)} listing{'s' if len(group)!=1 else ''})")
        lines.append("="*40)
        for l in group:
            deal = l.get("deal") or {}
            deal_str = f"  Deal:     {deal.get('label','')} (${abs(deal.get('delta',0)):,} {'below' if deal.get('delta',0)<0 else 'above'} market)\n" if deal.get("label") else ""
            lines.append(
                f"\n{l['title']}\n"
                f"  Price:    ${l['price']:,}\n"
                f"  Mileage:  {l['miles']:,} mi\n"
                f"  Location: {l['city']}, {l['state']} ({l['distance']:.0f} mi away)\n"
                f"  Source:   {l['source']}\n"
                f"{deal_str}"
                f"  Link:     {l['url']}\n"
            )
    return "\n".join(lines)

def send_alert(search: dict, listings: list[dict]) -> None:
    if not listings:
        return
    recipients = [e.strip() for e in search.get("alert_emails", "").split(",") if e.strip()]
    if not recipients:
        return  # no valid email, skip
    resend.api_key = RESEND_API_KEY
    body = build_email_body(search, listings)
    n = len(listings)
    subject = f"[CarFinder] {n} new {search['model']} match{'es' if n!=1 else ''} found"
    resend.Emails.send({
        "from": RESEND_FROM,
        "to": ", ".join(recipients),
        "subject": subject,
        "text": body,
    })
    print(f"[email] Sent: {subject} → {', '.join(recipients)}")
