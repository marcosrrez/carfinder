# Trim & Drivetrain Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the free-text trim field with a multi-select trim picker backed by a curated hand-written dataset, wire trim + drivetrain filters into the Marketcheck scanner, and add a scorer boost for trim matches.

**Architecture:** Pure frontend for the UI (TrimSelector component + trim-data.ts dataset already written), backend DB migration for two new columns (trims, drivetrain), and targeted scanner/scorer updates. No new dependencies.

**Tech Stack:** React 18, TypeScript 5, Flask, SQLite, Marketcheck API

---

## File Structure

```
carfinder-ui/src/
├── data/
│   └── trim-data.ts          ALREADY WRITTEN — 1,200-line curated trim dataset
├── components/
│   └── TrimSelector.tsx      NEW — multi-select trim UI with drivetrain radio
├── screens/
│   └── SetupScreen.tsx       MODIFY — replace trim text input with TrimSelector
├── types.ts                  MODIFY — trim: string → trims: string[], add drivetrain: string
├── api.ts                    MODIFY — toSnake/fromSnake for trims + drivetrain

carfinder/
├── models.py                 MODIFY — add trims + drivetrain columns + migration
├── api/searches.py           MODIFY — setdefault trims + drivetrain
├── scanner/marketcheck.py    MODIFY — pass trim list + drivetrain to Marketcheck API
├── scorer.py                 MODIFY — add trim_matches() helper function
├── api/listings.py           MODIFY — include trimMatch in listing response
├── tests/test_scorer.py      MODIFY — add trim_matches tests
├── tests/test_scanner.py     MODIFY — add trim/drivetrain filter tests
```

---

## Task 1: trim-data.ts ✅ ALREADY COMPLETE

The file `/Users/marcos/carfinder-ui/src/data/trim-data.ts` has been written (1,210 lines).
It exports: `TrimOption`, `Drivetrain`, `ModelTrims`, `loadTrimData()`, `getTrims()`, `hasTrimData()`.
Covers 60+ models across 20+ makes.

- [ ] **Step 1: Commit the file**

```bash
cd /Users/marcos/carfinder-ui
git add src/data/trim-data.ts
git commit -m "feat: add curated trim dataset — 60+ models, 300+ trims with descriptions"
```

---

## Task 2: Backend DB migration

**Files:**
- Modify: `carfinder/models.py`
- Modify: `carfinder/api/searches.py`
- Test: `carfinder/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

In `/Users/marcos/carfinder/tests/test_models.py`, add after existing tests:

```python
def test_searches_has_trims_and_drivetrain_columns(tmp_db):
    """searches table has trims and drivetrain columns."""
    row = tmp_db.execute("PRAGMA table_info(searches)").fetchall()
    col_names = [r[1] for r in row]
    assert "trims" in col_names
    assert "drivetrain" in col_names

def test_create_search_stores_trims_and_drivetrain(tmp_db):
    """create_search round-trips trims and drivetrain."""
    import tempfile, os
    from models import Database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        data = {
            "user_id": "u1", "make": "Toyota", "model": "Highlander",
            "trim": "", "year": 2016, "max_price": 25000, "ideal_price": 20000,
            "max_miles": 130000, "ideal_miles": 90000, "zip": "72761",
            "city": "Siloam Springs", "radius_miles": 100,
            "interval_hours": 2, "alert_emails": "a@test.com",
            "trims": "XLE,Limited", "drivetrain": "AWD",
        }
        result = db.create_search(data)
        assert result["trims"] == "XLE,Limited"
        assert result["drivetrain"] == "AWD"
        db.close()
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_models.py::test_searches_has_trims_and_drivetrain_columns tests/test_models.py::test_create_search_stores_trims_and_drivetrain -v
```

Expected: FAIL (columns don't exist yet)

- [ ] **Step 3: Update models.py**

In `_create_tables`, inside the CREATE TABLE searches statement, add after `trim TEXT DEFAULT '',`:

```sql
trims TEXT NOT NULL DEFAULT '',
drivetrain TEXT NOT NULL DEFAULT 'Any',
```

After the existing alert_emails migration block, add:

```python
# Migrate: add trims and drivetrain columns
for col_def in [
    "trims TEXT NOT NULL DEFAULT ''",
    "drivetrain TEXT NOT NULL DEFAULT 'Any'",
]:
    try:
        self.conn.execute(f"ALTER TABLE searches ADD COLUMN {col_def}")
        self.conn.commit()
    except Exception:
        pass
# Copy existing single trim into trims column
try:
    self.conn.execute(
        "UPDATE searches SET trims = trim WHERE trims = '' AND trim != ''"
    )
    self.conn.commit()
except Exception:
    pass
```

In `create_search`, the INSERT statement currently has 17 columns ending with `alert_emails, active, created_at`. Add `trims` and `drivetrain` before `active`:

```python
self.conn.execute("""
    INSERT INTO searches
    (id, user_id, make, model, trim, year, max_price, ideal_price,
     max_miles, ideal_miles, zip, city, radius_miles, interval_hours,
     alert_emails, trims, drivetrain, active, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)
""", (search_id, data["user_id"], data["make"], data["model"],
      data.get("trim", ""), data["year"], data["max_price"],
      data["ideal_price"], data["max_miles"], data["ideal_miles"],
      data["zip"], data["city"], data["radius_miles"],
      data["interval_hours"], data["alert_emails"],
      data.get("trims", ""), data.get("drivetrain", "Any"), now))
```

In `update_search`, add `"trims"` and `"drivetrain"` to the `fields` list:

```python
fields = ["make", "model", "trim", "year", "max_price", "ideal_price",
          "max_miles", "ideal_miles", "zip", "city", "radius_miles",
          "interval_hours", "alert_emails", "trims", "drivetrain"]
```

- [ ] **Step 4: Update api/searches.py**

In `create_search`, add after existing setdefaults:

```python
data.setdefault("trims", "")
data.setdefault("drivetrain", "Any")
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_models.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder
git add models.py api/searches.py tests/test_models.py
git commit -m "feat: add trims and drivetrain columns to searches table"
```

---

## Task 3: Scanner trim + drivetrain filter

**Files:**
- Modify: `carfinder/scanner/marketcheck.py`
- Test: `carfinder/tests/test_scanner.py`

- [ ] **Step 1: Write the failing tests**

In `/Users/marcos/carfinder/tests/test_scanner.py`, add:

```python
from unittest.mock import patch, MagicMock

def test_fetch_zip_passes_trim_and_drivetrain_when_set():
    """Scanner passes trim list and drivetrain to Marketcheck when set."""
    search = {
        "id": "s1", "year": 2016, "make": "Toyota", "model": "Highlander",
        "max_price": 25000, "max_miles": 130000,
        "trims": "XLE,Limited", "drivetrain": "AWD",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"listings": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("scanner.marketcheck.requests.get", return_value=mock_resp) as mock_get:
        from scanner.marketcheck import _fetch_zip
        _fetch_zip(search, "72761")
        call_params = mock_get.call_args[1]["params"]
        assert call_params.get("trim") == "XLE,Limited"
        assert call_params.get("drivetrain") == "AWD"

def test_fetch_zip_omits_trim_and_drivetrain_when_empty():
    """Scanner does not send trim or drivetrain when they are empty/Any."""
    search = {
        "id": "s1", "year": 2016, "make": "Toyota", "model": "Highlander",
        "max_price": 25000, "max_miles": 130000,
        "trims": "", "drivetrain": "Any",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"listings": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("scanner.marketcheck.requests.get", return_value=mock_resp) as mock_get:
        from scanner.marketcheck import _fetch_zip
        _fetch_zip(search, "72761")
        call_params = mock_get.call_args[1]["params"]
        assert "trim" not in call_params
        assert "drivetrain" not in call_params
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_scanner.py::test_fetch_zip_passes_trim_and_drivetrain_when_set tests/test_scanner.py::test_fetch_zip_omits_trim_and_drivetrain_when_empty -v
```

Expected: FAIL

- [ ] **Step 3: Update scanner/marketcheck.py**

In `_fetch_zip`, after the existing `params` dict is defined, add:

```python
# Trim filter — Marketcheck accepts comma-separated trim values (OR logic)
trims_str = search.get("trims", "")
if trims_str:
    params["trim"] = trims_str

# Drivetrain filter — AND filter applied on top of trim selection
drivetrain = search.get("drivetrain", "Any")
if drivetrain and drivetrain != "Any":
    params["drivetrain"] = drivetrain
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_scanner.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder
git add scanner/marketcheck.py tests/test_scanner.py
git commit -m "feat: pass trim and drivetrain filters to Marketcheck scanner"
```

---

## Task 4: Scorer trim match helper

**Files:**
- Modify: `carfinder/scorer.py`
- Modify: `carfinder/api/listings.py`
- Modify: `carfinder/tests/test_scorer.py`

- [ ] **Step 1: Write the failing tests**

In `/Users/marcos/carfinder/tests/test_scorer.py`, add:

```python
from scorer import trim_matches

def test_trim_matches_when_listing_trim_in_selected():
    listing = {"trim": "XLE Premium", "title": "2016 Toyota Highlander XLE Premium"}
    search = {"trims": "XLE,Limited"}
    assert trim_matches(listing, search) is True

def test_trim_matches_uses_title_as_fallback():
    listing = {"trim": "", "title": "2016 Toyota Highlander XLE AWD"}
    search = {"trims": "XLE"}
    assert trim_matches(listing, search) is True

def test_trim_no_match():
    listing = {"trim": "LE", "title": "2016 Toyota Highlander LE"}
    search = {"trims": "XLE,Limited"}
    assert trim_matches(listing, search) is False

def test_trim_empty_trims_returns_false():
    listing = {"trim": "XLE", "title": ""}
    search = {"trims": ""}
    assert trim_matches(listing, search) is False

def test_trim_no_trims_key_returns_false():
    listing = {"trim": "XLE", "title": ""}
    search = {}
    assert trim_matches(listing, search) is False
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_scorer.py::test_trim_matches_when_listing_trim_in_selected -v
```

Expected: FAIL with ImportError (trim_matches not defined yet)

- [ ] **Step 3: Add trim_matches to scorer.py**

Add this function to the bottom of `/Users/marcos/carfinder/scorer.py`:

```python
def trim_matches(listing: dict, search: dict) -> bool:
    """True if the listing's trim matches any of the search's selected trims."""
    trims_str = search.get("trims", "")
    if not trims_str:
        return False
    selected = [t.strip().lower() for t in trims_str.split(",") if t.strip()]
    if not selected:
        return False
    # Check trim field first, fall back to title
    text = (listing.get("trim") or listing.get("title") or "").lower()
    return any(t in text for t in selected)
```

- [ ] **Step 4: Update api/listings.py to include trimMatch**

In `api/listings.py`, update the import line:

```python
from scorer import score_listing, deal_for, trim_matches
```

In the result.append call, add `"trimMatch"`:

```python
result.append({
    **l,
    "tier": tier,
    "deal": deal,
    "saved": l["id"] in saved_ids,
    "trimMatch": trim_matches(l, search),
})
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_scorer.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder
git add scorer.py api/listings.py tests/test_scorer.py
git commit -m "feat: add trim_matches scorer helper, expose trimMatch in listings API"
```

---

## Task 5: Frontend types.ts + api.ts

**Files:**
- Modify: `carfinder-ui/src/types.ts`
- Modify: `carfinder-ui/src/api.ts`

- [ ] **Step 1: Update types.ts**

Read `/Users/marcos/carfinder-ui/src/types.ts` first.

Replace `trim: string` with `trims: string[]` in the `Search` interface. Add `drivetrain: string` after `trims`. Add `trimMatch?: boolean` to `EnrichedListing`.

The updated Search interface:

```ts
export interface Search {
  id: string;
  year: number;
  make: string;
  model: string;
  trims: string[];       // was: trim: string
  drivetrain: string;    // "Any" | "FWD" | "AWD" | "4WD" | "RWD"
  maxPrice: number;
  idealPrice: number;
  maxMiles: number;
  idealMiles: number;
  zip: string;
  city: string;
  radius: number;
  intervalHours: number;
  alertEmails: string[];
  active: boolean;
}
```

Add to EnrichedListing:

```ts
export interface EnrichedListing extends Listing {
  tier: TierKey;
  deal: Deal;
  searchId: string;
  trimMatch?: boolean;
}
```

- [ ] **Step 2: Update api.ts toSnake**

Read `/Users/marcos/carfinder-ui/src/api.ts` first.

In `toSnake`, replace `trim: s.trim ?? ""` with:

```ts
trims:      (s.trims ?? []).join(","),
drivetrain: s.drivetrain ?? "Any",
```

- [ ] **Step 3: Update api.ts fromSnake**

In `fromSnake`, replace `trim: (r.trim ?? "") as string` with:

```ts
trims:      ((r.trims ?? r.trim ?? "") as string)
              .split(",").map((t: string) => t.trim()).filter(Boolean),
drivetrain: (r.drivetrain ?? "Any") as string,
```

- [ ] **Step 4: Run build to find broken references**

```bash
cd /Users/marcos/carfinder-ui && npm run build 2>&1 | grep -E "error|Error"
```

Fix every error. Common locations: `SetupScreen.tsx` has `f.trim` references, `DEFAULT` object has `trim: ""`.

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/types.ts src/api.ts src/screens/SetupScreen.tsx
git commit -m "feat: update Search type — trim: string → trims: string[], add drivetrain"
```

---

## Task 6: TrimSelector component

**Files:**
- Create: `carfinder-ui/src/components/TrimSelector.tsx`

- [ ] **Step 1: Create TrimSelector.tsx**

```tsx
// carfinder-ui/src/components/TrimSelector.tsx
import { useState, useEffect } from "react";
import { loadTrimData, getTrims, hasTrimData } from "../data/trim-data";
import type { TrimOption, Drivetrain } from "../data/trim-data";

const ALL_DRIVETRAINS: Array<{ value: "Any" | Drivetrain; label: string }> = [
  { value: "Any", label: "Any" },
  { value: "FWD", label: "FWD" },
  { value: "AWD", label: "AWD" },
  { value: "4WD", label: "4WD" },
  { value: "RWD", label: "RWD" },
];

interface Props {
  make: string;
  model: string;
  selectedTrims: string[];
  drivetrain: string;
  onTrimsChange: (trims: string[]) => void;
  onDrivetrainChange: (d: string) => void;
}

export function TrimSelector({ make, model, selectedTrims, drivetrain, onTrimsChange, onDrivetrainChange }: Props) {
  const [trims, setTrims] = useState<TrimOption[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!make || !model) { setTrims([]); return; }
    setLoading(true);
    loadTrimData().then(() => {
      setTrims(getTrims(make, model));
      setLoading(false);
    });
  }, [make, model]);

  if (!make || !model) return null;

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "12px 0" }}>
        {[1, 2, 3].map((i) => (
          <div key={i} style={{ height: 52, borderRadius: 8, background: "rgba(255,255,255,.04)" }} />
        ))}
      </div>
    );
  }

  // If model not in dataset, return null — SetupScreen shows text fallback
  if (trims.length === 0) return null;

  const anySelected = selectedTrims.length === 0;

  const toggle = (name: string) => {
    if (selectedTrims.includes(name)) {
      onTrimsChange(selectedTrims.filter((t) => t !== name));
    } else {
      onTrimsChange([...selectedTrims, name]);
    }
  };

  // Only show drivetrains that exist for this model
  const availableDrivetrainValues = new Set(trims.flatMap((t) => t.drivetrains));
  const visibleDrivetrains = ALL_DRIVETRAINS.filter(
    (d) => d.value === "Any" || availableDrivetrainValues.has(d.value as Drivetrain)
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Drivetrain radio */}
      <div>
        <div style={{ fontSize: 13, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em", marginBottom: 8 }}>
          Drivetrain
        </div>
        <div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}>
          {visibleDrivetrains.map((d) => (
            <button
              key={d.value}
              type="button"
              onClick={() => onDrivetrainChange(d.value)}
              style={{
                padding: "5px 14px", borderRadius: 99, fontSize: 13, fontWeight: 500,
                border: drivetrain === d.value ? "1px solid var(--blue)" : "1px solid var(--line-2)",
                background: drivetrain === d.value ? "rgba(0,122,255,.12)" : "transparent",
                color: drivetrain === d.value ? "var(--blue)" : "var(--fg-muted)",
                cursor: "pointer", letterSpacing: "-0.01em", transition: "all 0.12s",
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Trim checkboxes */}
      <div>
        <div style={{ fontSize: 13, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em", marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
          Trims
          {anySelected && (
            <span style={{ fontSize: 11, fontWeight: 500, color: "var(--fg-subtle)", background: "rgba(255,255,255,.07)", borderRadius: 99, padding: "1px 8px" }}>
              Any trim
            </span>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          {trims.map((trim) => {
            const checked = selectedTrims.includes(trim.name);
            const incompatible = drivetrain !== "Any" && !trim.drivetrains.includes(drivetrain as Drivetrain);
            return (
              <label
                key={trim.name}
                style={{
                  display: "flex", alignItems: "flex-start", gap: 12, padding: "10px 13px",
                  borderRadius: 9, cursor: "pointer",
                  border: checked ? "1px solid rgba(255,255,255,.14)" : "1px solid var(--line)",
                  background: checked ? "rgba(255,255,255,.04)" : "transparent",
                  opacity: incompatible ? 0.38 : 1,
                  transition: "all 0.12s",
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(trim.name)}
                  disabled={incompatible}
                  style={{ marginTop: 3, accentColor: "var(--blue)", flexShrink: 0, cursor: "pointer" }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 13.5, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em" }}>
                      {trim.name}
                    </span>
                    {trim.badge && (
                      <span style={{ fontSize: 11, fontWeight: 500, color: "var(--fg-subtle)", background: "rgba(255,255,255,.07)", borderRadius: 99, padding: "1px 7px", flexShrink: 0 }}>
                        {trim.badge}
                      </span>
                    )}
                    <span style={{ fontSize: 11.5, color: "var(--fg-subtle)", marginLeft: "auto", flexShrink: 0 }}>
                      {trim.drivetrains.join(" · ")}
                      {incompatible && (
                        <span style={{ color: "var(--amber)", marginLeft: 6 }}>
                          not in {drivetrain}
                        </span>
                      )}
                    </span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--fg-muted)", lineHeight: 1.5, letterSpacing: "-0.005em" }}>
                    {trim.description}
                  </div>
                </div>
              </label>
            );
          })}
        </div>

        {!anySelected && (
          <button
            type="button"
            onClick={() => onTrimsChange([])}
            style={{ marginTop: 8, fontSize: 12.5, color: "var(--fg-subtle)", background: "none", border: "none", cursor: "pointer", padding: 0, letterSpacing: "-0.01em" }}
          >
            Clear — show any trim
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/components/TrimSelector.tsx
git commit -m "feat: add TrimSelector component with drivetrain radio and trim checkboxes"
```

---

## Task 7: SetupScreen integration

**Files:**
- Modify: `carfinder-ui/src/screens/SetupScreen.tsx`

- [ ] **Step 1: Read the current SetupScreen.tsx**

Read `/Users/marcos/carfinder-ui/src/screens/SetupScreen.tsx` before making any changes.

- [ ] **Step 2: Update DEFAULT and imports**

Add import at top of file:

```tsx
import { TrimSelector } from "../components/TrimSelector";
import { hasTrimData } from "../data/trim-data";
```

In the `DEFAULT` object, replace `trim: ""` with:

```ts
trims: [],
drivetrain: "Any",
```

- [ ] **Step 3: Replace the Trim field in the Vehicle section**

Find the current Trim field (currently a plain `<Field label="Trim"...>` with a text input). Replace the entire `<Field label="Trim" ...>` block with:

```tsx
{/* Trim & Drivetrain selector — full width */}
<div style={{ gridColumn: "span 6", marginTop: 6 }}>
  <TrimSelector
    make={f.make ?? ""}
    model={f.model ?? ""}
    selectedTrims={f.trims ?? []}
    drivetrain={f.drivetrain ?? "Any"}
    onTrimsChange={(trims) => setF((s) => ({ ...s, trims }))}
    onDrivetrainChange={(drivetrain) => setF((s) => ({ ...s, drivetrain }))}
  />
  {/* Free-text fallback when model not in dataset */}
  {f.make && f.model && !hasTrimData(f.make, f.model) && (
    <div style={{ marginTop: 8 }}>
      <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em" }}>
          Trim <span style={{ color: "var(--fg-subtle)", fontWeight: 450 }}>optional</span>
        </span>
        <input
          className="cf-input"
          value={(f.trims ?? []).join(", ")}
          onChange={(e) =>
            setF((s) => ({
              ...s,
              trims: e.target.value.split(",").map((t) => t.trim()).filter(Boolean),
            }))
          }
          placeholder="e.g. XLE Premium"
        />
      </label>
    </div>
  )}
</div>
```

- [ ] **Step 4: Run build and fix all errors**

```bash
cd /Users/marcos/carfinder-ui && npm run build 2>&1 | tail -30
```

Fix any remaining TypeScript errors. Look for:
- References to `f.trim` (change to `f.trims`)
- References to `search.trim` (change to `search.trims?.[0] ?? ""`)
- `hasTrimData` needing data to be loaded — note: `hasTrimData` works only after `loadTrimData()` is called. Since `loadTrimData()` is already called in `useEffect` on mount, the free-text fallback may briefly show on first render. This is acceptable — add `loaded` state if it flickers noticeably.

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/screens/SetupScreen.tsx
git commit -m "feat: wire TrimSelector into SetupScreen, replace free-text trim input"
```

---

## Task 8: Deploy both services

- [ ] **Step 1: Run full backend test suite**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: all PASS

- [ ] **Step 2: Run frontend build**

```bash
cd /Users/marcos/carfinder-ui && npm run build 2>&1 | tail -10
```

Expected: clean build, no errors

- [ ] **Step 3: Deploy backend to Railway**

```bash
cd /Users/marcos/carfinder && source ~/.railway/env && railway up --service CarFinder --detach
```

- [ ] **Step 4: Deploy frontend to Vercel**

```bash
cd /Users/marcos/carfinder-ui && vercel --prod --yes 2>&1 | tail -5
```

- [ ] **Step 5: Smoke test**

1. Open https://carfinder-ui.vercel.app
2. Click "New search"
3. Select Make: Toyota, Model: Highlander
4. Trim selector appears — drivetrain radios (Any/FWD/AWD) and trim checkboxes with descriptions
5. Select AWD → LE and LE Plus remain visible but dimmed (not available in AWD)
6. Check XLE → badge shows "Most popular", description visible
7. Check Limited → "Any trim" chip disappears, two trims selected
8. Submit — search saved with trims and drivetrain
9. Scanner respects the trim and drivetrain filter on next scan

---

## Self-Review

**Spec coverage:**
- ✅ Multi-select trim checkboxes — Task 6, 7
- ✅ Per-trim descriptions (hand-written) — Task 1 (trim-data.ts)
- ✅ Per-trim drivetrain availability — Task 1, 6
- ✅ Global drivetrain AND-filter — Task 6, 7, 3
- ✅ OR logic for multiple trims — Task 3 (comma-separated to Marketcheck)
- ✅ "Any trim" chip when nothing selected — Task 6
- ✅ Incompatible trims dimmed when drivetrain selected — Task 6
- ✅ Free-text fallback for models not in dataset — Task 7
- ✅ DB migration: trims + drivetrain columns — Task 2
- ✅ Scanner filter — Task 3
- ✅ Scorer trim_matches helper — Task 4
- ✅ trimMatch exposed in listings API — Task 4
- ✅ Frontend types updated — Task 5

**No placeholders found.**

**Type consistency:** `TrimOption`, `Drivetrain`, `ModelTrims` defined in Task 1 trim-data.ts. Used in Task 6 TrimSelector with matching import paths. `getTrims()` and `hasTrimData()` defined in Task 1, used in Task 6 and Task 7. `Search.trims: string[]` and `Search.drivetrain: string` defined in Task 5, used in Task 7 SetupScreen. All consistent.
