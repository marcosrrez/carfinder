import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_EMAIL, SEARCH

TIER_LABELS = {"ideal": "⭐ IDEAL", "good": "✓ GOOD", "ok": "~ OK"}
TIER_ORDER = ["ideal", "good", "ok"]

def build_email_body(listings: list[dict]) -> str:
    grouped = {tier: [] for tier in TIER_ORDER}
    for listing in listings:
        grouped[listing["score"]].append(listing)

    lines = [f"{len(listings)} new match(es) for your {SEARCH['year']} {SEARCH['make']} {SEARCH['model']} search.\n"]
    for tier in TIER_ORDER:
        group = grouped[tier]
        if not group:
            continue
        lines.append(f"\n{'='*40}")
        lines.append(f"{TIER_LABELS[tier]} ({len(group)} listing{'s' if len(group) != 1 else ''})")
        lines.append("="*40)
        for listing in group:
            lines.append(
                f"\n{listing['title']}\n"
                f"  Price:    ${listing['price']:,}\n"
                f"  Mileage:  {listing['miles']:,} mi\n"
                f"  Location: {listing['city']}, {listing['state']} ({listing['distance']:.0f} mi away)\n"
                f"  Source:   {listing['source']}\n"
                f"  Link:     {listing['url']}\n"
            )
    return "\n".join(lines)

def send_alert(listings: list[dict]) -> None:
    if not listings:
        return

    body = build_email_body(listings)
    subject = f"[CarFinder] {len(listings)} new {SEARCH['model']} match{'es' if len(listings) != 1 else ''} found"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ALERT_EMAIL
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, ALERT_EMAIL, msg.as_string())
    print(f"[email] Sent alert: {subject}")
