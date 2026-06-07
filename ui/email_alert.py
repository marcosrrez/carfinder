# email_alert.py
import resend
from config import RESEND_API_KEY, RESEND_FROM

TIER_CONFIG = {
    "ideal": {"label": "Ideal",  "color": "#34c759", "bg": "rgba(52,199,89,.12)",  "border": "rgba(52,199,89,.25)"},
    "good":  {"label": "Good",   "color": "#0a84ff", "bg": "rgba(10,132,255,.12)", "border": "rgba(10,132,255,.25)"},
    "ok":    {"label": "Ok",     "color": "#ff9f0a", "bg": "rgba(255,159,10,.12)", "border": "rgba(255,159,10,.25)"},
}
TIER_ORDER = ["ideal", "good", "ok"]


def _listing_card(listing: dict, tier: str) -> str:
    cfg = TIER_CONFIG.get(tier, TIER_CONFIG["ok"])
    title = listing.get("title", "")
    price = f"${listing.get('price', 0):,}"
    miles = f"{listing.get('miles', 0):,} mi"
    city  = listing.get("city", "")
    state = listing.get("state", "")
    dist  = listing.get("distance", 0)
    url   = listing.get("url", "#")
    drv   = listing.get("drivetrain", "")
    ext   = listing.get("exterior", "")
    days  = listing.get("days_listed")
    drop_amount = listing.get("drop_amount")
    drop_when   = listing.get("drop_when", "")
    seller_type = listing.get("seller_type", "")

    location_str = f"{city}, {state}" if city and state else city or state
    if dist:
        location_str += f" &nbsp;·&nbsp; {int(dist)} mi away"

    meta_parts = []
    if drv:      meta_parts.append(drv)
    if ext:      meta_parts.append(ext)
    if days is not None: meta_parts.append(f"{days}d listed")
    if seller_type:      meta_parts.append(seller_type)
    meta_str = " &nbsp;·&nbsp; ".join(meta_parts)

    drop_html = ""
    if drop_amount and drop_amount > 0:
        drop_html = f"""
        <div style="margin:10px 0 0;padding:7px 10px;border-radius:6px;background:rgba(52,199,89,.1);border:1px solid rgba(52,199,89,.2);font-size:12px;color:#34c759;font-weight:500;">
          ↓ Price dropped ${drop_amount:,} {f"({drop_when})" if drop_when else ""}
        </div>"""

    return f"""
    <div style="margin:12px 0;border-radius:12px;background:#1c1c1e;border:1px solid #2c2c2e;overflow:hidden;">
      <div style="padding:14px 16px 0;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
          <div style="flex:1;min-width:0;">
            <div style="font-size:15px;font-weight:600;color:#f5f5f7;letter-spacing:-0.02em;line-height:1.3;margin-bottom:4px;">{title}</div>
            <div style="font-size:12.5px;color:#8e8e93;letter-spacing:-0.01em;">{location_str}</div>
          </div>
          <div style="text-align:right;flex-shrink:0;">
            <div style="font-size:18px;font-weight:700;color:#f5f5f7;letter-spacing:-0.03em;">{price}</div>
            <div style="font-size:12px;color:#8e8e93;margin-top:1px;">{miles}</div>
          </div>
        </div>
        {f'<div style="margin-top:8px;font-size:12px;color:#636366;letter-spacing:-0.01em;">{meta_str}</div>' if meta_str else ""}
        {drop_html}
      </div>
      <div style="padding:12px 16px;">
        <a href="{url}" style="display:inline-block;padding:8px 16px;border-radius:8px;background:{cfg['color']};color:#000;font-size:13px;font-weight:600;text-decoration:none;letter-spacing:-0.01em;">View listing →</a>
      </div>
    </div>"""


def _tier_section(tier: str, listings: list[dict]) -> str:
    cfg = TIER_CONFIG[tier]
    count = len(listings)
    cards = "".join(_listing_card(l, tier) for l in listings)
    return f"""
    <div style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{cfg['color']};flex-shrink:0;"></span>
        <span style="font-size:13px;font-weight:600;color:{cfg['color']};letter-spacing:-0.01em;text-transform:uppercase;">{cfg['label']}</span>
        <span style="font-size:12px;color:#636366;">— {count} listing{"s" if count != 1 else ""}</span>
      </div>
      {cards}
    </div>"""


def build_email_html(search: dict, listings: list[dict]) -> str:
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    n = len(listings)

    grouped = {tier: [] for tier in TIER_ORDER}
    for listing in listings:
        tier = listing.get("tier", "ok")
        if tier in grouped:
            grouped[tier].append(listing)

    sections = "".join(
        _tier_section(tier, grouped[tier])
        for tier in TIER_ORDER
        if grouped[tier]
    )

    headline = f"{n} new match{'es' if n != 1 else ''} for your {vehicle} search"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CarFinder — {headline}</title>
</head>
<body style="margin:0;padding:0;background:#000000;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#000000;min-height:100vh;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" style="max-width:560px;" cellpadding="0" cellspacing="0">

          <!-- Header -->
          <tr>
            <td style="padding-bottom:28px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
                <span style="font-size:20px;font-weight:700;color:#f5f5f7;letter-spacing:-0.03em;">CarFinder</span>
                <span style="font-size:12px;color:#636366;font-weight:500;padding:2px 8px;border-radius:99px;border:1px solid #2c2c2e;">Alert</span>
              </div>
              <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;color:#f5f5f7;letter-spacing:-0.04em;line-height:1.2;">{headline}</h1>
              <p style="margin:0;font-size:14px;color:#636366;letter-spacing:-0.01em;">These just appeared — act fast, good ones go quick.</p>
            </td>
          </tr>

          <!-- Listings -->
          <tr>
            <td>
              {sections}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding-top:28px;border-top:1px solid #1c1c1e;">
              <p style="margin:0 0 4px;font-size:12px;color:#48484a;letter-spacing:-0.01em;">
                You're receiving this because you set up a CarFinder search for <strong style="color:#636366;">{vehicle}</strong>.
              </p>
              <p style="margin:0;font-size:12px;color:#48484a;letter-spacing:-0.01em;">
                Manage your searches at <a href="https://carfinder-ui.vercel.app" style="color:#636366;text-decoration:none;">carfinder-ui.vercel.app</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_email_text(search: dict, listings: list[dict]) -> str:
    """Plain-text fallback."""
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    lines = [f"{len(listings)} new match(es) for your {vehicle} search.\n"]
    for tier in TIER_ORDER:
        group = [l for l in listings if l.get("tier", "ok") == tier]
        if not group:
            continue
        label = TIER_CONFIG[tier]["label"].upper()
        lines.append(f"\n── {label} ({len(group)}) ──")
        for l in group:
            drop = f"  ↓ Price dropped ${l['drop_amount']:,}\n" if l.get("drop_amount") else ""
            lines.append(
                f"\n{l.get('title','')}\n"
                f"  ${l.get('price',0):,}  ·  {l.get('miles',0):,} mi\n"
                f"  {l.get('city','')}, {l.get('state','')} ({int(l.get('distance',0))} mi)\n"
                f"{drop}"
                f"  {l.get('url','')}\n"
            )
    return "\n".join(lines)


def send_alert(search: dict, listings: list[dict]) -> None:
    if not listings:
        return
    recipients = [e.strip() for e in search.get("alert_emails", "").split(",") if e.strip()]
    if not recipients:
        return
    resend.api_key = RESEND_API_KEY
    n = len(listings)
    vehicle = f"{search['year']} {search['make']} {search['model']}"
    subject = f"🔍 {n} new {vehicle} match{'es' if n != 1 else ''} found"
    resend.Emails.send({
        "from": RESEND_FROM,
        "to": recipients,
        "subject": subject,
        "html": build_email_html(search, listings),
        "text": build_email_text(search, listings),
    })
    print(f"[email] Sent: {subject} → {', '.join(recipients)}")
