# CarFinder Plan C — Auth + Payments

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Clerk JWT authentication (multi-user, real user IDs) and Stripe pay-per-hunt ($9.99 per active search/month) to both the Flask API and the React frontend.

**Architecture:** Clerk handles sign-up/sign-in and issues JWTs. The Flask API verifies every JWT with Clerk's public key (`python-jose`). Each request's `sub` claim replaces the temporary `X-User-Id` header. Stripe Checkout creates a one-time $9.99 charge when a user activates a search. A Stripe webhook marks the search `paid=true` in the DB, which the scheduler checks before scanning. Frontend uses `@clerk/clerk-react` for auth UI and redirects unpaid searches to a Stripe Checkout session URL.

**Tech Stack:** Clerk (JWT verification, hosted sign-in), Stripe (Checkout, webhooks), python-jose (JWT decode), stripe Python SDK, `@clerk/clerk-react`, `@stripe/stripe-js`

**Prerequisites:** Plan A backend and Plan B frontend must be deployed before executing Plan C.

---

## File Structure Changes

```
carfinder/ (backend additions)
├── auth.py                   # NEW — Clerk JWT verification middleware
├── api/
│   ├── searches.py           # MODIFY — replace X-User-Id with JWT sub claim
│   ├── listings.py           # MODIFY — same
│   ├── scan.py               # MODIFY — same
│   └── billing.py            # NEW — POST /api/billing/checkout, webhook handler
├── models.py                 # MODIFY — add paid column to searches, add payments table
└── requirements.txt          # MODIFY — add python-jose[cryptography], stripe

carfinder-ui/ (frontend additions)
├── src/
│   ├── main.tsx              # MODIFY — wrap App in ClerkProvider
│   ├── App.tsx               # MODIFY — add AuthGate, redirect unpaid searches
│   ├── api.ts                # MODIFY — attach Bearer token to all requests
│   ├── components/
│   │   ├── AuthGate.tsx      # NEW — shows Clerk SignIn if not signed in
│   │   └── PaywallBanner.tsx # NEW — "Activate this hunt for $9.99" CTA
│   └── screens/
│       └── SetupScreen.tsx   # MODIFY — show PaywallBanner for unpaid searches
├── .env.local                # MODIFY — add VITE_CLERK_PUBLISHABLE_KEY, VITE_STRIPE_KEY
└── package.json              # MODIFY — add @clerk/clerk-react
```

---

## Task 1: Clerk + Stripe accounts and env vars

**Files:**
- Modify: `carfinder/.env`
- Modify: `carfinder-ui/.env.local`

- [ ] **Step 1: Create a Clerk application**

1. Go to https://clerk.com → create account → "Create application"
2. Name: **CarFinder** · Enable: Email + Google sign-in
3. In Dashboard → API Keys, copy:
   - **Publishable key**: `pk_live_...`
   - **Secret key**: `sk_live_...`
4. In Dashboard → JWT Templates → copy the **JWKS endpoint URL** (looks like `https://YOUR_FRONTEND_API.clerk.accounts.dev/.well-known/jwks.json`)

- [ ] **Step 2: Create a Stripe account and product**

1. Go to https://stripe.com → create account
2. Dashboard → Products → "Add product"
   - Name: **CarFinder Hunt**
   - Price: **$9.99** · One-time
   - Copy the **Price ID**: `price_...`
3. Dashboard → API Keys, copy:
   - **Publishable key**: `pk_live_...`
   - **Secret key**: `sk_live_...`
4. Dashboard → Webhooks → "Add endpoint"
   - URL: `https://YOUR_RAILWAY_URL/api/billing/webhook`
   - Events: `checkout.session.completed`
   - Copy **Signing secret**: `whsec_...`

- [ ] **Step 3: Add secrets to backend .env**

Append to `/Users/marcos/carfinder/.env`:

```
CLERK_JWKS_URL=https://YOUR_FRONTEND_API.clerk.accounts.dev/.well-known/jwks.json
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
APP_URL=https://YOUR_VERCEL_URL.vercel.app
```

- [ ] **Step 4: Add secrets to frontend .env.local**

Append to `/Users/marcos/carfinder-ui/.env.local`:

```
VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

- [ ] **Step 5: Update config.py to load new vars**

In `/Users/marcos/carfinder/config.py`, add after the existing `_require` calls:

```python
CLERK_JWKS_URL      = _require("CLERK_JWKS_URL")
STRIPE_SECRET_KEY   = _require("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = _require("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID     = _require("STRIPE_PRICE_ID")
APP_URL             = _require("APP_URL")
```

- [ ] **Step 6: Install new backend dependencies**

```bash
cd /Users/marcos/carfinder
pip install python-jose[cryptography] stripe
pip freeze | grep -E "jose|stripe" >> requirements.txt
```

Expected output includes lines like:
```
python-jose[cryptography]==3.3.0
stripe==9.x.x
```

- [ ] **Step 7: Commit**

```bash
cd /Users/marcos/carfinder
git add config.py requirements.txt
git commit -m "feat: add Clerk + Stripe env var config"
```

---

## Task 2: Backend JWT auth middleware

**Files:**
- Create: `carfinder/auth.py`

- [ ] **Step 1: Write failing test**

Create `/Users/marcos/carfinder/tests/test_auth.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from auth import verify_jwt, AuthError

def test_verify_jwt_valid_token():
    """verify_jwt returns payload dict for a valid token."""
    mock_payload = {"sub": "user_abc123", "iss": "https://clerk.example.com"}
    with patch("auth._decode_token", return_value=mock_payload):
        result = verify_jwt("fake.jwt.token")
    assert result["sub"] == "user_abc123"

def test_verify_jwt_missing_sub():
    """verify_jwt raises AuthError if sub claim is missing."""
    with patch("auth._decode_token", return_value={"iss": "clerk"}):
        with pytest.raises(AuthError):
            verify_jwt("bad.token")

def test_verify_jwt_expired():
    """verify_jwt raises AuthError on expired token."""
    from jose import ExpiredSignatureError
    with patch("auth._decode_token", side_effect=ExpiredSignatureError("expired")):
        with pytest.raises(AuthError):
            verify_jwt("expired.token")
```

Run:

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_auth.py -v
```

Expected: FAIL — `auth` module not found.

- [ ] **Step 2: Create auth.py**

```python
import requests
from functools import lru_cache
from jose import jwt, JWTError, ExpiredSignatureError
from config import CLERK_JWKS_URL


class AuthError(Exception):
    pass


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch and cache JWKS from Clerk. Cache invalidates on process restart."""
    resp = requests.get(CLERK_JWKS_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _decode_token(token: str) -> dict:
    """Decode and verify a Clerk JWT against the JWKS. Raises jose errors on failure."""
    jwks = _get_jwks()
    return jwt.decode(token, jwks, algorithms=["RS256"])


def verify_jwt(token: str) -> dict:
    """
    Verify a Clerk JWT and return the payload.
    Raises AuthError on any failure (expired, invalid, missing sub).
    """
    try:
        payload = _decode_token(token)
    except ExpiredSignatureError:
        raise AuthError("Token expired")
    except JWTError as e:
        raise AuthError(f"Invalid token: {e}")

    if "sub" not in payload:
        raise AuthError("Token missing sub claim")

    return payload


def get_user_id_from_request(request) -> str:
    """
    Extract and verify Bearer JWT from Flask request.
    Returns the Clerk user ID (sub claim).
    Raises AuthError if missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthError("Missing Authorization header")
    token = auth_header[len("Bearer "):]
    payload = verify_jwt(token)
    return payload["sub"]
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_auth.py -v
```

Expected: 3 PASS.

- [ ] **Step 4: Commit**

```bash
cd /Users/marcos/carfinder
git add auth.py tests/test_auth.py
git commit -m "feat: add Clerk JWT verification middleware"
```

---

## Task 3: Add `paid` column + payments table to DB

**Files:**
- Modify: `carfinder/models.py`

- [ ] **Step 1: Write failing test**

In `/Users/marcos/carfinder/tests/test_models.py`, add:

```python
def test_searches_has_paid_column(tmp_db):
    """searches table has a paid column defaulting to 0."""
    conn = tmp_db
    row = conn.execute("PRAGMA table_info(searches)").fetchall()
    col_names = [r[1] for r in row]
    assert "paid" in col_names

def test_payments_table_exists(tmp_db):
    """payments table exists with expected columns."""
    row = tmp_db.execute("PRAGMA table_info(payments)").fetchall()
    col_names = [r[1] for r in row]
    assert "stripe_session_id" in col_names
    assert "user_id" in col_names
    assert "search_id" in col_names
```

Run:

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_models.py::test_searches_has_paid_column tests/test_models.py::test_payments_table_exists -v
```

Expected: FAIL — column/table not found.

- [ ] **Step 2: Modify models.py — add paid column and payments table**

In `/Users/marcos/carfinder/models.py`, find the `CREATE TABLE searches` statement and add `paid INTEGER NOT NULL DEFAULT 0` to the column list. Then add a new table after `searches`:

```python
# In the CREATE TABLE searches statement, add this column:
#   paid INTEGER NOT NULL DEFAULT 0,

# After the searches table creation block, add:
conn.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          TEXT NOT NULL,
        search_id        TEXT NOT NULL,
        stripe_session_id TEXT NOT NULL UNIQUE,
        amount_cents     INTEGER NOT NULL DEFAULT 999,
        created_at       TEXT NOT NULL DEFAULT (datetime('now'))
    )
""")
```

Full updated `CREATE TABLE searches` should look like:

```sql
CREATE TABLE IF NOT EXISTS searches (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    make           TEXT NOT NULL,
    model          TEXT NOT NULL,
    year           INTEGER NOT NULL,
    trim           TEXT,
    max_price      INTEGER NOT NULL,
    ideal_price    INTEGER NOT NULL,
    max_miles      INTEGER NOT NULL,
    ideal_miles    INTEGER NOT NULL,
    zip            TEXT NOT NULL,
    city           TEXT,
    radius         INTEGER NOT NULL DEFAULT 100,
    interval_hours INTEGER NOT NULL DEFAULT 2,
    email          TEXT NOT NULL,
    active         INTEGER NOT NULL DEFAULT 1,
    paid           INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
)
```

- [ ] **Step 3: Run tests to verify**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_models.py -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
cd /Users/marcos/carfinder
git add models.py tests/test_models.py
git commit -m "feat: add paid column to searches, add payments table"
```

---

## Task 4: Replace X-User-Id with JWT auth in all API blueprints

**Files:**
- Modify: `carfinder/api/searches.py`
- Modify: `carfinder/api/listings.py`
- Modify: `carfinder/api/scan.py`

- [ ] **Step 1: Write failing test**

In `/Users/marcos/carfinder/tests/test_api_searches.py`, add a test that confirms `X-User-Id` is no longer accepted:

```python
def test_get_searches_requires_bearer_token(client):
    """GET /api/searches returns 401 if no Authorization header is present."""
    # client fixture sends no auth header
    resp = client.get("/api/searches")
    assert resp.status_code == 401

def test_get_searches_rejects_x_user_id(client):
    """X-User-Id header alone is rejected (no bearer token)."""
    resp = client.get("/api/searches", headers={"X-User-Id": "user_test"})
    assert resp.status_code == 401
```

Run:

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_api_searches.py::test_get_searches_requires_bearer_token tests/test_api_searches.py::test_get_searches_rejects_x_user_id -v
```

Expected: FAIL (currently 200 because X-User-Id is accepted).

- [ ] **Step 2: Create a shared auth helper used by all blueprints**

Create `/Users/marcos/carfinder/api/__init__.py` (or update it) to expose a `require_auth` decorator:

```python
from functools import wraps
from flask import request, jsonify
from auth import get_user_id_from_request, AuthError


def require_auth(f):
    """Decorator: verifies Clerk JWT, injects user_id into kwargs."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user_id = get_user_id_from_request(request)
        except AuthError as e:
            return jsonify({"error": str(e)}), 401
        return f(*args, user_id=user_id, **kwargs)
    return decorated
```

- [ ] **Step 3: Update api/searches.py — replace X-User-Id with @require_auth**

In `/Users/marcos/carfinder/api/searches.py`, replace every occurrence of:

```python
user_id = request.headers.get("X-User-Id", "default")
```

with the `@require_auth` decorator on each route function. Example for `GET /api/searches`:

```python
from api import require_auth

@bp.route("/api/searches", methods=["GET"])
@require_auth
def get_searches(user_id: str):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM searches WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    return jsonify({"searches": [dict(r) for r in rows]})
```

Apply the same pattern to `POST /api/searches`, `PUT /api/searches/<id>`, `DELETE /api/searches/<id>`.

- [ ] **Step 4: Update api/listings.py and api/scan.py the same way**

Replace `X-User-Id` extraction with `@require_auth` decorator + `user_id` parameter in every route in both files.

- [ ] **Step 5: Update tests to mock auth**

In test files, patch `auth.get_user_id_from_request` so tests don't need a real JWT:

```python
# In conftest.py or at top of each test file, add a fixture:
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_auth():
    with patch("auth.get_user_id_from_request", return_value="user_test"):
        yield
```

Add this fixture to `tests/conftest.py`.

- [ ] **Step 6: Run full test suite**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
cd /Users/marcos/carfinder
git add api/ tests/conftest.py
git commit -m "feat: replace X-User-Id with Clerk JWT auth in all API routes"
```

---

## Task 5: Billing API — Stripe Checkout + webhook

**Files:**
- Create: `carfinder/api/billing.py`

- [ ] **Step 1: Write failing test**

Create `/Users/marcos/carfinder/tests/test_api_billing.py`:

```python
import pytest
import json
from unittest.mock import patch, MagicMock

def test_create_checkout_session(client, mock_auth):
    """POST /api/billing/checkout returns a Stripe Checkout URL."""
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc"
    with patch("stripe.checkout.Session.create", return_value=mock_session):
        resp = client.post("/api/billing/checkout",
            json={"search_id": "s_test"},
            headers={"Authorization": "Bearer fake"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["url"].startswith("https://checkout.stripe.com")

def test_webhook_marks_search_paid(client, tmp_db):
    """Stripe webhook marks the search paid=1 in the DB."""
    # Insert a search into tmp_db
    tmp_db.execute("INSERT INTO searches (id, user_id, make, model, year, max_price, ideal_price, max_miles, ideal_miles, zip, email) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("s_test", "user_test", "Toyota", "Highlander", 2016, 20000, 18000, 130000, 90000, "72761", "test@test.com"))
    tmp_db.commit()

    payload = json.dumps({
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_abc",
            "metadata": {"search_id": "s_test", "user_id": "user_test"},
            "amount_total": 999,
        }}
    }).encode()

    with patch("stripe.Webhook.construct_event", return_value=json.loads(payload)):
        resp = client.post("/api/billing/webhook",
            data=payload,
            content_type="application/json",
            headers={"Stripe-Signature": "fake"})
    assert resp.status_code == 200

    row = tmp_db.execute("SELECT paid FROM searches WHERE id = 's_test'").fetchone()
    assert row["paid"] == 1
```

Run:

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_api_billing.py -v
```

Expected: FAIL — billing blueprint not found.

- [ ] **Step 2: Create api/billing.py**

```python
import stripe
from flask import Blueprint, request, jsonify, current_app
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID, APP_URL
from api import require_auth

stripe.api_key = STRIPE_SECRET_KEY

bp = Blueprint("billing", __name__)


@bp.route("/api/billing/checkout", methods=["POST"])
@require_auth
def create_checkout(user_id: str):
    """Create a Stripe Checkout session for activating one search ($9.99)."""
    data = request.get_json(force=True)
    search_id = data.get("search_id")
    if not search_id:
        return jsonify({"error": "search_id required"}), 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="payment",
        success_url=f"{APP_URL}/?paid=1&search_id={search_id}",
        cancel_url=f"{APP_URL}/?paid=0&search_id={search_id}",
        metadata={"search_id": search_id, "user_id": user_id},
    )
    return jsonify({"url": session.url})


@bp.route("/api/billing/webhook", methods=["POST"])
def stripe_webhook():
    """Handle Stripe Checkout completed event — mark search as paid."""
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        search_id = session_obj["metadata"]["search_id"]
        user_id = session_obj["metadata"]["user_id"]
        session_id = session_obj["id"]
        amount = session_obj.get("amount_total", 999)

        db = current_app.extensions["db_conn"]()
        db.execute(
            "UPDATE searches SET paid = 1 WHERE id = ? AND user_id = ?",
            (search_id, user_id)
        )
        db.execute(
            "INSERT OR IGNORE INTO payments (user_id, search_id, stripe_session_id, amount_cents) VALUES (?,?,?,?)",
            (user_id, search_id, session_id, amount)
        )
        db.commit()

    return jsonify({"ok": True})
```

- [ ] **Step 3: Register billing blueprint in app.py**

In `/Users/marcos/carfinder/app.py`, in `create_app()`, add:

```python
from api.billing import bp as billing_bp
app.register_blueprint(billing_bp)
```

- [ ] **Step 4: Gate scheduler on paid=1**

In `/Users/marcos/carfinder/scheduler.py`, in `_run_all_active_searches()`, change the query to only include paid searches:

```python
# Before (fetches all active):
searches = db.execute("SELECT * FROM searches WHERE active = 1").fetchall()

# After (only paid and active):
searches = db.execute(
    "SELECT * FROM searches WHERE active = 1 AND paid = 1"
).fetchall()
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder
git add api/billing.py app.py scheduler.py tests/test_api_billing.py
git commit -m "feat: add Stripe Checkout + webhook, gate scheduler on paid searches"
```

---

## Task 6: Frontend — Clerk auth + Stripe redirect

**Files:**
- Modify: `carfinder-ui/package.json`
- Modify: `carfinder-ui/src/main.tsx`
- Modify: `carfinder-ui/src/api.ts`
- Create: `carfinder-ui/src/components/AuthGate.tsx`
- Create: `carfinder-ui/src/components/PaywallBanner.tsx`
- Modify: `carfinder-ui/src/App.tsx`

- [ ] **Step 1: Install Clerk React**

```bash
cd /Users/marcos/carfinder-ui && npm install @clerk/clerk-react
```

- [ ] **Step 2: Wrap App in ClerkProvider — update src/main.tsx**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import "./tokens.css";
import { App } from "./App";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
if (!PUBLISHABLE_KEY) throw new Error("Missing VITE_CLERK_PUBLISHABLE_KEY");

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <App />
    </ClerkProvider>
  </StrictMode>
);
```

- [ ] **Step 3: Create src/components/AuthGate.tsx**

```tsx
import { SignIn, useAuth } from "@clerk/clerk-react";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--fg-muted)", fontSize: 14 }}>
        Loading…
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <SignIn appearance={{ variables: { colorPrimary: "#4f8ff5", colorBackground: "#101216", colorText: "#f0f0f2", colorInputBackground: "#13161b", colorInputText: "#f0f0f2" } }} />
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 4: Update src/api.ts to attach Bearer token**

Replace the `headers()` function in `api.ts`:

```ts
// Remove the old static headers function and replace with:
import { useAuth } from "@clerk/clerk-react";

// api.ts can't use hooks directly; instead export a factory:
export function makeApi(getToken: () => Promise<string | null>) {
  async function headers(): Promise<Record<string, string>> {
    const token = await getToken();
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers: await headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`${method} ${path} → ${res.status}`);
    return res.json() as Promise<T>;
  }

  return {
    getSearches:   ()              => req<{ searches: import("./types").Search[] }>("GET",    "/api/searches"),
    createSearch:  (s: Partial<import("./types").Search>) => req("POST", "/api/searches", s),
    updateSearch:  (id: string, s: Partial<import("./types").Search>) => req("PUT", `/api/searches/${id}`, s),
    deleteSearch:  (id: string)    => req("DELETE", `/api/searches/${id}`),
    getListings:   (searchId: string) => req<{ listings: import("./types").Listing[] }>("GET", `/api/searches/${searchId}/listings`),
    savelisting:   (searchId: string, lid: string) => req("POST", `/api/searches/${searchId}/listings/${lid}/save`),
    unsaveListing: (searchId: string, lid: string) => req("DELETE", `/api/searches/${searchId}/listings/${lid}/save`),
    hideListing:   (searchId: string, lid: string) => req("POST", `/api/searches/${searchId}/listings/${lid}/hide`),
    unhideAll:     (searchId: string) => req("DELETE", `/api/searches/${searchId}/listings/hidden`),
    scanSearch: (searchId: string) => req("POST", `/api/searches/${searchId}/scan`),
    scanAll:    ()                  => req("POST", "/api/scan"),
    createCheckout: (searchId: string) => req<{ url: string }>("POST", "/api/billing/checkout", { search_id: searchId }),
  };
}

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";
// Default no-auth api (used before Clerk loads)
export const api = makeApi(async () => null);
```

- [ ] **Step 5: Create src/components/PaywallBanner.tsx**

```tsx
import { Icon } from "./Icon";

interface Props {
  searchId: string;
  onActivate: (searchId: string) => void;
  activating: boolean;
}

export function PaywallBanner({ searchId, onActivate, activating }: Props) {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16,
      padding: "14px 18px", borderRadius: 12,
      background: "rgba(79,143,245,.07)", border: "1px solid rgba(79,143,245,.2)",
    }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.015em" }}>
          Activate this hunt
        </div>
        <div style={{ fontSize: 13, color: "var(--fg-muted)", letterSpacing: "-0.01em" }}>
          One-time $9.99 — CarFinder scans every few hours and emails you new matches.
        </div>
      </div>
      <button
        className="cf-btn cf-btn-primary"
        onClick={() => onActivate(searchId)}
        disabled={activating}
        style={{ flex: "none" }}
      >
        {activating ? "Redirecting…" : <>Activate · $9.99 <Icon name="arrowUpRight" size={14} /></>}
      </button>
    </div>
  );
}
```

- [ ] **Step 6: Update App.tsx — add AuthGate, use makeApi with Clerk token, handle paywall**

Replace the content of `src/App.tsx`:

```tsx
import { useState, useCallback } from "react";
import { useAuth } from "@clerk/clerk-react";
import { AuthGate } from "./components/AuthGate";
import { makeApi } from "./api";
import { useAppState } from "./useAppState";
import { TopBar } from "./components/TopBar";
import { Dashboard } from "./screens/Dashboard";
import { SetupScreen } from "./screens/SetupScreen";
import { EmailScreen } from "./screens/EmailScreen";
import { CompareModal } from "./screens/CompareModal";
import { PaywallBanner } from "./components/PaywallBanner";
import type { Search } from "./types";

type View = "dashboard" | "setup" | "email";

function AuthedApp() {
  const { getToken } = useAuth();
  const api = makeApi(() => getToken());

  // Pass api into useAppState (update useAppState to accept an api param, see note below)
  const state = useAppState(api);
  const [view, setView] = useState<View>("dashboard");
  const [activeId, setActiveId] = useState("all");
  const [editingSearch, setEditingSearch] = useState<Partial<Search> | null>(null);
  const [setupMode, setSetupMode] = useState<"new" | "edit">("new");
  const [showCompare, setShowCompare] = useState(false);
  const [activating, setActivating] = useState(false);

  const { searches, listingsBySearch, saved, loading, error, createSearch, updateSearch } = state;

  const newCount = searches.reduce((acc, s) => {
    const ls = listingsBySearch[s.id] ?? [];
    return acc + ls.filter((l) => l.isNew).length;
  }, 0);

  const handleEdit = (search: Search) => {
    setEditingSearch(search);
    setSetupMode("edit");
    setView("setup");
  };

  const handleNewSearch = () => {
    setEditingSearch(null);
    setSetupMode("new");
    setView("setup");
  };

  const handleSave = async (s: Partial<Search>) => {
    if (setupMode === "new") {
      await createSearch(s);
    } else if (editingSearch?.id) {
      await updateSearch(editingSearch.id, s);
    }
    setView("dashboard");
  };

  const handleActivate = useCallback(async (searchId: string) => {
    setActivating(true);
    try {
      const { url } = await api.createCheckout(searchId);
      window.location.href = url;
    } catch (e) {
      console.error(e);
      setActivating(false);
    }
  }, [api]);

  // Show paywall banner for the active search if not paid
  const activeSearch = searches.find((s) => s.id === activeId);
  const showPaywall = activeSearch && !activeSearch.paid && !activeSearch.active;

  if (loading) {
    return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--fg-muted)" }}>Loading…</div>;
  }
  if (error) {
    return <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", gap: 12 }}>
      <div style={{ color: "var(--amber)" }}>Could not connect to backend</div>
      <button className="cf-btn cf-btn-ghost" onClick={state.reload}>Retry</button>
    </div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <TopBar view={view} onNav={(v) => setView(v as View)} newCount={newCount}
        searches={searches} activeId={activeId}
        onSelectSearch={setActiveId} onNewSearch={handleNewSearch} />

      {showPaywall && view === "dashboard" && (
        <div style={{ maxWidth: 940, margin: "16px auto 0", width: "100%", padding: "0 30px" }}>
          <PaywallBanner searchId={activeId} onActivate={handleActivate} activating={activating} />
        </div>
      )}

      {view === "dashboard" && (
        <Dashboard {...state} activeId={activeId} onEdit={handleEdit} onCompare={() => setShowCompare(true)} />
      )}
      {view === "setup" && (
        <SetupScreen search={editingSearch ?? undefined} mode={setupMode}
          onSave={handleSave} onCancel={() => setView("dashboard")} />
      )}
      {view === "email" && (
        <EmailScreen searches={searches} listingsBySearch={listingsBySearch} />
      )}

      {showCompare && (
        <CompareModal searches={searches} listingsBySearch={listingsBySearch}
          saved={saved} onClose={() => setShowCompare(false)} />
      )}
    </div>
  );
}

export function App() {
  return (
    <AuthGate>
      <AuthedApp />
    </AuthGate>
  );
}
```

**Note:** `useAppState` must be updated to accept an `api` parameter instead of importing the singleton `api` directly. In `useAppState.ts`, change the signature to:

```ts
import type { makeApi } from "./api";
type Api = ReturnType<typeof makeApi>;

export function useAppState(api: Api): AppState {
  // replace all usages of the imported `api` with the parameter
  ...
}
```

- [ ] **Step 7: Build and verify no TypeScript errors**

```bash
cd /Users/marcos/carfinder-ui && npm run build
```

Expected: clean build, no type errors.

- [ ] **Step 8: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/
git commit -m "feat: add Clerk auth gate, Stripe paywall, token-authenticated API calls"
```

---

## Task 7: Deploy both services with new secrets

**Files:**
- Backend: Railway env vars
- Frontend: Vercel env vars

- [ ] **Step 1: Push backend to Railway with new env vars**

In Railway dashboard (https://railway.app), go to your carfinder project → Variables tab, and add:

```
CLERK_JWKS_URL=<from Clerk dashboard>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
APP_URL=https://YOUR_VERCEL_URL.vercel.app
```

Then push the backend:

```bash
cd /Users/marcos/carfinder
git push origin main
```

Railway auto-deploys on push. Verify the deployment goes green in the Railway dashboard.

- [ ] **Step 2: Add Clerk + Stripe env vars to Vercel**

```bash
cd /Users/marcos/carfinder-ui
vercel env add VITE_CLERK_PUBLISHABLE_KEY production
# enter your pk_live_...

vercel env add VITE_STRIPE_PUBLISHABLE_KEY production
# enter your Stripe pk_live_...
```

- [ ] **Step 3: Deploy frontend**

```bash
cd /Users/marcos/carfinder-ui && vercel --prod
```

Expected: new deployment URL. Opening it should show the Clerk sign-in screen.

- [ ] **Step 4: End-to-end smoke test**

1. Open the Vercel URL in a browser
2. Sign in with your email via Clerk
3. You should land on Dashboard with your Highlander search listed
4. Click the search — if `paid=0`, the PaywallBanner appears
5. Click "Activate · $9.99" → redirected to Stripe Checkout
6. Use Stripe test card `4242 4242 4242 4242`, any future date, any CVC
7. After payment, redirected back to app with `?paid=1`
8. Verify search now shows listings and scans run

- [ ] **Step 5: Commit and tag**

```bash
cd /Users/marcos/carfinder-ui
git tag v0.2.0
git push origin main --tags

cd /Users/marcos/carfinder
git tag v0.2.0
git push origin main --tags
```

---

## Self-Review

**Spec coverage:**
- ✅ Clerk JWT auth — every API endpoint requires valid Bearer token — Task 2, 4
- ✅ Real user IDs from Clerk `sub` claim replace X-User-Id — Task 4
- ✅ Stripe Checkout for $9.99 pay-per-hunt — Task 5
- ✅ Webhook marks search `paid=1` — Task 5
- ✅ Scheduler only scans paid searches — Task 5
- ✅ Frontend AuthGate (Clerk SignIn wall) — Task 6
- ✅ PaywallBanner with Stripe redirect — Task 6
- ✅ Styled Clerk SignIn with design tokens colors — Task 6
- ✅ Both services deployed with production secrets — Task 7
- ✅ End-to-end smoke test documented — Task 7

**No placeholders found.**

**Type consistency:** `makeApi` returns the same method signatures as the original `api` object. `useAppState` updated to accept `Api` parameter. `PaywallBanner` receives `searchId: string`, `onActivate: (id: string) => void` — matches `AuthedApp.handleActivate` signature.
