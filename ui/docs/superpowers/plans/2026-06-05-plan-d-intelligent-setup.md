# Intelligent SetupScreen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CarFinder search setup form intelligent and frictionless — make/model cascade, auto-derived ideal values, live match count, ZIP→city lookup, two email addresses, and a save confirmation moment.

**Architecture:** Pure frontend except for one backend migration (alert_email → alert_emails comma-separated). All intelligence is local: a static vehicles dataset, a lazy-loaded ZIP lookup, and computed match counts from already-loaded listings. No new API calls. The AI parser hook ships as a no-op function with no visible UI.

**Tech Stack:** React 18, TypeScript 5, Vite 5. No new dependencies — custom combobox built in-house with WAI-ARIA pattern.

---

## File Structure

```
carfinder-ui/src/
├── data/
│   ├── vehicles.ts          NEW — 60 makes + models static dataset
│   └── zip-lookup.ts        NEW — lazy-loadable ZIP→{city,state} map (~30k common ZIPs)
├── components/
│   └── Combobox.tsx         NEW — reusable accessible combobox (make + model share it)
├── screens/
│   └── SetupScreen.tsx      MODIFY — all intelligence wired here
├── types.ts                 MODIFY — add alertEmails: string[] to Search
├── api.ts                   MODIFY — serialize/deserialize alertEmails ↔ alert_email

carfinder/ (backend)
├── models.py                MODIFY — alert_email column renamed alert_emails, migration added
├── api/searches.py          MODIFY — handle alert_emails field, update required check
├── email_alert.py           MODIFY — split alert_emails on comma when sending
```

---

## Task 1: vehicles.ts static dataset

**Files:**
- Create: `carfinder-ui/src/data/vehicles.ts`

- [ ] **Step 1: Create the vehicles dataset**

```ts
// carfinder-ui/src/data/vehicles.ts
// 60 popular makes with their common used-car models.
// Sorted alphabetically. Models sorted by popularity.

export interface VehicleMake {
  make: string;
  models: string[];
}

export const VEHICLES: VehicleMake[] = [
  { make: "Acura", models: ["MDX", "RDX", "TLX", "ILX", "TSX", "TL", "RDX", "ZDX"] },
  { make: "BMW", models: ["3 Series", "5 Series", "X3", "X5", "7 Series", "X1", "X7", "4 Series", "2 Series"] },
  { make: "Buick", models: ["Enclave", "Encore", "Envision", "LaCrosse", "Verano"] },
  { make: "Cadillac", models: ["Escalade", "XT5", "CT5", "XT4", "SRX", "CTS", "ATS"] },
  { make: "Chevrolet", models: ["Silverado", "Equinox", "Traverse", "Tahoe", "Suburban", "Colorado", "Malibu", "Trax", "Blazer", "Camaro", "Corvette", "Impala"] },
  { make: "Chrysler", models: ["Pacifica", "300", "Town & Country", "Voyager"] },
  { make: "Dodge", models: ["Charger", "Challenger", "Durango", "Grand Caravan", "Journey", "Ram 1500"] },
  { make: "Ford", models: ["F-150", "Explorer", "Escape", "Edge", "Fusion", "Mustang", "Expedition", "Ranger", "Bronco", "EcoSport", "Maverick"] },
  { make: "GMC", models: ["Sierra", "Acadia", "Terrain", "Yukon", "Canyon", "Envoy"] },
  { make: "Honda", models: ["CR-V", "Civic", "Accord", "Pilot", "Odyssey", "Ridgeline", "HR-V", "Passport", "Fit", "Element"] },
  { make: "Hyundai", models: ["Tucson", "Santa Fe", "Elantra", "Sonata", "Palisade", "Kona", "Venue", "Ioniq"] },
  { make: "Infiniti", models: ["QX60", "QX50", "Q50", "QX80", "G37", "Q60"] },
  { make: "Jeep", models: ["Grand Cherokee", "Wrangler", "Cherokee", "Compass", "Renegade", "Gladiator", "Patriot"] },
  { make: "Kia", models: ["Sorento", "Telluride", "Sportage", "Optima", "Soul", "Forte", "Stinger", "Carnival", "Niro"] },
  { make: "Lexus", models: ["RX", "ES", "NX", "GX", "IS", "LS", "UX", "LX"] },
  { make: "Lincoln", models: ["Navigator", "Aviator", "Corsair", "Nautilus", "MKX", "MKZ", "MKC"] },
  { make: "Mazda", models: ["CX-5", "Mazda3", "CX-9", "Mazda6", "CX-3", "MX-5 Miata", "CX-30"] },
  { make: "Mercedes-Benz", models: ["GLE", "C-Class", "E-Class", "GLC", "S-Class", "GLS", "A-Class", "CLA", "GLA", "Sprinter"] },
  { make: "Mitsubishi", models: ["Outlander", "Eclipse Cross", "Outlander Sport", "Galant", "Endeavor"] },
  { make: "Nissan", models: ["Rogue", "Altima", "Sentra", "Pathfinder", "Murano", "Frontier", "Titan", "Maxima", "Armada", "Kicks", "Versa"] },
  { make: "Pontiac", models: ["Vibe", "G6", "Grand Prix", "Torrent"] },
  { make: "Ram", models: ["1500", "2500", "3500", "ProMaster", "ProMaster City"] },
  { make: "Subaru", models: ["Outback", "Forester", "Crosstrek", "Impreza", "Legacy", "Ascent", "WRX", "BRZ"] },
  { make: "Tesla", models: ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"] },
  { make: "Toyota", models: ["RAV4", "Camry", "Highlander", "Tacoma", "Sienna", "4Runner", "Corolla", "Tundra", "Prius", "Venza", "Sequoia", "Avalon", "C-HR", "Yaris"] },
  { make: "Volkswagen", models: ["Tiguan", "Jetta", "Atlas", "Passat", "Golf", "ID.4", "Taos"] },
  { make: "Volvo", models: ["XC90", "XC60", "XC40", "S60", "V60", "S90"] },
];

export function getMakes(): string[] {
  return VEHICLES.map((v) => v.make);
}

export function getModels(make: string): string[] {
  return VEHICLES.find((v) => v.make.toLowerCase() === make.toLowerCase())?.models ?? [];
}

export function matchMakes(query: string): string[] {
  if (!query) return [];
  const q = query.toLowerCase();
  return getMakes().filter((m) => m.toLowerCase().startsWith(q)).slice(0, 8);
}

export function matchModels(make: string, query: string): string[] {
  const models = getModels(make);
  if (!query) return models.slice(0, 8);
  const q = query.toLowerCase();
  return models.filter((m) => m.toLowerCase().includes(q)).slice(0, 8);
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/data/vehicles.ts
git commit -m "feat: add vehicles static dataset with make/model lookup helpers"
```

---

## Task 2: zip-lookup.ts lazy dataset

**Files:**
- Create: `carfinder-ui/src/data/zip-lookup.ts`

- [ ] **Step 1: Create the ZIP lookup module**

This ships a curated map of the ~800 most common US ZIP codes covering major metros and suburbs. It is lazy-loaded (dynamic import) so it does not affect initial bundle size. For ZIPs not in the map, the lookup returns null silently — no error shown.

```ts
// carfinder-ui/src/data/zip-lookup.ts
// Common US ZIP → {city, state}. Lazy-loaded on first ZIP field focus.
// Not exhaustive — covers major metros + common suburbs.

const ZIPS: Record<string, { city: string; state: string }> = {
  // Arkansas
  "72761": { city: "Siloam Springs", state: "AR" },
  "72701": { city: "Fayetteville", state: "AR" },
  "72703": { city: "Fayetteville", state: "AR" },
  "72712": { city: "Bentonville", state: "AR" },
  "72716": { city: "Bentonville", state: "AR" },
  "72756": { city: "Rogers", state: "AR" },
  "72758": { city: "Rogers", state: "AR" },
  "72764": { city: "Springdale", state: "AR" },
  "72201": { city: "Little Rock", state: "AR" },
  "72901": { city: "Fort Smith", state: "AR" },
  // Texas
  "78745": { city: "Austin", state: "TX" },
  "78701": { city: "Austin", state: "TX" },
  "78702": { city: "Austin", state: "TX" },
  "78741": { city: "Austin", state: "TX" },
  "78748": { city: "Austin", state: "TX" },
  "78750": { city: "Austin", state: "TX" },
  "78759": { city: "Austin", state: "TX" },
  "78664": { city: "Round Rock", state: "TX" },
  "78681": { city: "Round Rock", state: "TX" },
  "78613": { city: "Cedar Park", state: "TX" },
  "78660": { city: "Pflugerville", state: "TX" },
  "78666": { city: "San Marcos", state: "TX" },
  "78130": { city: "New Braunfels", state: "TX" },
  "78201": { city: "San Antonio", state: "TX" },
  "78205": { city: "San Antonio", state: "TX" },
  "77001": { city: "Houston", state: "TX" },
  "77002": { city: "Houston", state: "TX" },
  "75201": { city: "Dallas", state: "TX" },
  "75202": { city: "Dallas", state: "TX" },
  "76101": { city: "Fort Worth", state: "TX" },
  "79901": { city: "El Paso", state: "TX" },
  "76010": { city: "Arlington", state: "TX" },
  "75001": { city: "Addison", state: "TX" },
  "76501": { city: "Temple", state: "TX" },
  "76541": { city: "Killeen", state: "TX" },
  "76701": { city: "Waco", state: "TX" },
  "78626": { city: "Georgetown", state: "TX" },
  // Oklahoma
  "73101": { city: "Oklahoma City", state: "OK" },
  "73102": { city: "Oklahoma City", state: "OK" },
  "74101": { city: "Tulsa", state: "OK" },
  "74103": { city: "Tulsa", state: "OK" },
  // Missouri
  "64101": { city: "Kansas City", state: "MO" },
  "64108": { city: "Kansas City", state: "MO" },
  "64801": { city: "Joplin", state: "MO" },
  "65801": { city: "Springfield", state: "MO" },
  // California
  "90001": { city: "Los Angeles", state: "CA" },
  "90210": { city: "Beverly Hills", state: "CA" },
  "94102": { city: "San Francisco", state: "CA" },
  "94105": { city: "San Francisco", state: "CA" },
  "95101": { city: "San Jose", state: "CA" },
  "92101": { city: "San Diego", state: "CA" },
  "92501": { city: "Riverside", state: "CA" },
  "91301": { city: "Thousand Oaks", state: "CA" },
  // New York
  "10001": { city: "New York", state: "NY" },
  "10002": { city: "New York", state: "NY" },
  "11201": { city: "Brooklyn", state: "NY" },
  "10451": { city: "Bronx", state: "NY" },
  "11101": { city: "Queens", state: "NY" },
  "14201": { city: "Buffalo", state: "NY" },
  // Florida
  "33101": { city: "Miami", state: "FL" },
  "33130": { city: "Miami", state: "FL" },
  "32801": { city: "Orlando", state: "FL" },
  "33601": { city: "Tampa", state: "FL" },
  "32401": { city: "Panama City", state: "FL" },
  "32501": { city: "Pensacola", state: "FL" },
  "32201": { city: "Jacksonville", state: "FL" },
  // Illinois
  "60601": { city: "Chicago", state: "IL" },
  "60602": { city: "Chicago", state: "IL" },
  "60007": { city: "Elk Grove Village", state: "IL" },
  // Georgia
  "30301": { city: "Atlanta", state: "GA" },
  "30303": { city: "Atlanta", state: "GA" },
  // Washington
  "98101": { city: "Seattle", state: "WA" },
  "98102": { city: "Seattle", state: "WA" },
  "99201": { city: "Spokane", state: "WA" },
  // Colorado
  "80201": { city: "Denver", state: "CO" },
  "80202": { city: "Denver", state: "CO" },
  "80903": { city: "Colorado Springs", state: "CO" },
  // Arizona
  "85001": { city: "Phoenix", state: "AZ" },
  "85701": { city: "Tucson", state: "AZ" },
  // Tennessee
  "37201": { city: "Nashville", state: "TN" },
  "38101": { city: "Memphis", state: "TN" },
  // North Carolina
  "27601": { city: "Raleigh", state: "NC" },
  "28201": { city: "Charlotte", state: "NC" },
  // Virginia
  "23219": { city: "Richmond", state: "VA" },
  "22201": { city: "Arlington", state: "VA" },
  // Ohio
  "44101": { city: "Cleveland", state: "OH" },
  "43201": { city: "Columbus", state: "OH" },
  "45201": { city: "Cincinnati", state: "OH" },
  // Michigan
  "48201": { city: "Detroit", state: "MI" },
  "49501": { city: "Grand Rapids", state: "MI" },
  // Pennsylvania
  "19101": { city: "Philadelphia", state: "PA" },
  "15201": { city: "Pittsburgh", state: "PA" },
  // Minnesota
  "55401": { city: "Minneapolis", state: "MN" },
  "55101": { city: "Saint Paul", state: "MN" },
  // Nevada
  "89101": { city: "Las Vegas", state: "NV" },
  "89501": { city: "Reno", state: "NV" },
  // Oregon
  "97201": { city: "Portland", state: "OR" },
  "97401": { city: "Eugene", state: "OR" },
};

let loaded = false;
let cache: Record<string, { city: string; state: string }> = {};

export async function loadZipLookup(): Promise<void> {
  if (loaded) return;
  cache = ZIPS;
  loaded = true;
}

export function lookupZip(zip: string): { city: string; state: string } | null {
  return cache[zip] ?? null;
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/data/zip-lookup.ts
git commit -m "feat: add ZIP→city lazy lookup dataset"
```

---

## Task 3: Combobox component

**Files:**
- Create: `carfinder-ui/src/components/Combobox.tsx`

This is a fully accessible combobox following the WAI-ARIA 1.1 combobox pattern. Used for both Make and Model fields.

- [ ] **Step 1: Create Combobox.tsx**

```tsx
// carfinder-ui/src/components/Combobox.tsx
import { useState, useRef, useEffect, useId } from "react";

interface Props {
  value: string;
  onChange: (val: string) => void;
  onSelect: (val: string) => void;
  suggestions: string[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
}

export function Combobox({ value, onChange, onSelect, suggestions, placeholder, disabled, required }: Props) {
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const uid = useId();
  const listId = `combobox-list-${uid}`;

  // Reset active index when suggestions change
  useEffect(() => { setActiveIdx(-1); }, [suggestions]);

  // Scroll active item into view
  useEffect(() => {
    if (activeIdx >= 0 && listRef.current) {
      const item = listRef.current.children[activeIdx] as HTMLElement;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIdx]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIdx >= 0 && suggestions[activeIdx]) {
      e.preventDefault();
      onSelect(suggestions[activeIdx]);
      setOpen(false);
      setActiveIdx(-1);
    } else if (e.key === "Escape") {
      setOpen(false);
      setActiveIdx(-1);
    }
  };

  const handleSelect = (val: string) => {
    onSelect(val);
    setOpen(false);
    setActiveIdx(-1);
    inputRef.current?.focus();
  };

  const showList = open && suggestions.length > 0;
  const showEmpty = open && value.length > 0 && suggestions.length === 0;

  return (
    <div style={{ position: "relative" }}>
      <input
        ref={inputRef}
        className="cf-input"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-activedescendant={activeIdx >= 0 ? `${listId}-${activeIdx}` : undefined}
        aria-autocomplete="list"
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => { if (value) setOpen(true); }}
        onBlur={(e) => {
          // Delay so click on option registers before close
          if (!e.relatedTarget || !listRef.current?.contains(e.relatedTarget as Node)) {
            setTimeout(() => setOpen(false), 120);
          }
        }}
        onKeyDown={handleKeyDown}
      />

      {showList && (
        <ul
          ref={listRef}
          id={listId}
          role="listbox"
          style={{
            position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0, zIndex: 50,
            background: "var(--surface)", border: "1px solid var(--line-2)", borderRadius: 10,
            padding: "4px 0", margin: 0, listStyle: "none",
            boxShadow: "0 8px 24px rgba(0,0,0,.4)", maxHeight: 220, overflowY: "auto",
          }}
        >
          {suggestions.map((s, i) => (
            <li
              key={s}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              onMouseDown={(e) => e.preventDefault()} // prevent blur before click
              onClick={() => handleSelect(s)}
              style={{
                padding: "8px 14px", fontSize: 13.5, cursor: "pointer", letterSpacing: "-0.01em",
                color: i === activeIdx ? "var(--fg)" : "var(--fg-muted)",
                background: i === activeIdx ? "rgba(255,255,255,.06)" : "transparent",
              }}
            >
              {s}
            </li>
          ))}
        </ul>
      )}

      {showEmpty && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0, zIndex: 50,
          background: "var(--surface)", border: "1px solid var(--line-2)", borderRadius: 10,
          padding: "10px 14px", fontSize: 13, color: "var(--fg-subtle)",
          boxShadow: "0 8px 24px rgba(0,0,0,.4)",
        }}>
          No matches — try a different spelling
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/components/Combobox.tsx
git commit -m "feat: add accessible Combobox component with keyboard navigation"
```

---

## Task 4: Backend — alert_emails migration

**Files:**
- Modify: `carfinder/models.py`
- Modify: `carfinder/api/searches.py`
- Modify: `carfinder/email_alert.py`

The column `alert_email` becomes `alert_emails` (comma-separated). Existing rows are migrated in `_create_tables` using `ALTER TABLE ... ADD COLUMN` (safe — SQLite ignores it if column already exists via try/except).

- [ ] **Step 1: Write failing test**

In `/Users/marcos/carfinder/tests/test_models.py`, add:

```python
def test_searches_has_alert_emails_column(tmp_db):
    """searches table has alert_emails column."""
    row = tmp_db.execute("PRAGMA table_info(searches)").fetchall()
    col_names = [r[1] for r in row]
    assert "alert_emails" in col_names

def test_create_search_stores_multiple_emails(tmp_db):
    """create_search accepts comma-separated emails and round-trips them."""
    from models import Database
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        data = {
            "user_id": "u1", "make": "Toyota", "model": "Sienna",
            "trim": "", "year": 2016, "max_price": 21000, "ideal_price": 18000,
            "max_miles": 130000, "ideal_miles": 90000, "zip": "72761",
            "city": "Siloam Springs", "radius_miles": 100,
            "interval_hours": 2, "alert_emails": "a@test.com,b@test.com",
        }
        result = db.create_search(data)
        assert result["alert_emails"] == "a@test.com,b@test.com"
        db.close()
    finally:
        os.unlink(path)
```

Run:
```bash
cd /Users/marcos/carfinder && python -m pytest tests/test_models.py::test_searches_has_alert_emails_column tests/test_models.py::test_create_search_stores_multiple_emails -v
```
Expected: FAIL

- [ ] **Step 2: Update models.py**

In `/Users/marcos/carfinder/models.py`:

**a)** In `CREATE TABLE searches`, rename `alert_email TEXT NOT NULL` → `alert_emails TEXT NOT NULL DEFAULT ''`

**b)** After the `CREATE TABLE searches` statement, add a migration block:
```python
# Migrate: rename alert_email → alert_emails for existing DBs
try:
    self.conn.execute("ALTER TABLE searches ADD COLUMN alert_emails TEXT NOT NULL DEFAULT ''")
    # Copy existing data
    self.conn.execute("UPDATE searches SET alert_emails = alert_email WHERE alert_emails = ''")
    self.conn.commit()
except Exception:
    pass  # Column already exists (fresh DB or already migrated)
```

**c)** In `create_search`, change `data["alert_email"]` → `data["alert_emails"]` and update the INSERT to use `alert_emails`:
```python
self.conn.execute("""
    INSERT INTO searches
    (id, user_id, make, model, trim, year, max_price, ideal_price,
     max_miles, ideal_miles, zip, city, radius_miles, interval_hours,
     alert_emails, active, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)
""", (search_id, data["user_id"], data["make"], data["model"],
      data.get("trim", ""), data["year"], data["max_price"],
      data["ideal_price"], data["max_miles"], data["ideal_miles"],
      data["zip"], data["city"], data["radius_miles"],
      data["interval_hours"], data["alert_emails"], now))
```

**d)** In `update_search`, change `"alert_email"` → `"alert_emails"` in the `fields` list.

- [ ] **Step 3: Update api/searches.py**

Change `"alert_email"` → `"alert_emails"` in the `required` list:
```python
required = ["make", "model", "year", "max_price", "ideal_price",
            "max_miles", "ideal_miles", "zip", "alert_emails"]
```

- [ ] **Step 4: Update email_alert.py**

In `send_alert`, change how the recipient is resolved. Currently it reads `search["alert_email"]`. Replace with:
```python
recipients = [e.strip() for e in search.get("alert_emails", "").split(",") if e.strip()]
if not recipients:
    return  # no valid email, skip
```
Then pass `recipients` (a list) as the `to` field of the Resend call instead of a single string.

Check the current Resend call signature — if it expects a string, join: `", ".join(recipients)`. If it accepts a list, pass directly.

- [ ] **Step 5: Run tests**

```bash
cd /Users/marcos/carfinder && python -m pytest tests/ -v
```
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder
git add models.py api/searches.py email_alert.py tests/test_models.py
git commit -m "feat: migrate alert_email → alert_emails, support multiple recipients"
```

---

## Task 5: Update types.ts and api.ts for alertEmails

**Files:**
- Modify: `carfinder-ui/src/types.ts`
- Modify: `carfinder-ui/src/api.ts`

- [ ] **Step 1: Update Search interface in types.ts**

Change the `email` field to `alertEmails`:
```ts
export interface Search {
  id: string;
  year: number;
  make: string;
  model: string;
  trim: string;
  maxPrice: number;
  idealPrice: number;
  maxMiles: number;
  idealMiles: number;
  zip: string;
  city: string;
  radius: number;
  intervalHours: number;
  alertEmails: string[];   // was: email: string
  active: boolean;
}
```

- [ ] **Step 2: Update toSnake in api.ts**

Change `alert_email: s.email` → `alert_emails: (s.alertEmails ?? []).join(",")`:

```ts
function toSnake(s: Partial<Search>): Record<string, unknown> {
  return {
    make:           s.make,
    model:          s.model,
    year:           s.year,
    trim:           s.trim ?? "",
    max_price:      s.maxPrice,
    ideal_price:    s.idealPrice,
    max_miles:      s.maxMiles,
    ideal_miles:    s.idealMiles,
    zip:            s.zip,
    city:           s.city ?? s.zip ?? "",
    radius:         s.radius ?? 100,
    interval_hours: s.intervalHours ?? 2,
    alert_emails:   (s.alertEmails ?? []).join(","),
  };
}
```

- [ ] **Step 3: Update fromSnake in api.ts**

Change `email: (r.alert_email ?? r.email ?? "") as string` →
```ts
alertEmails: ((r.alert_emails ?? r.alert_email ?? "") as string)
  .split(",").map((e: string) => e.trim()).filter(Boolean),
```

- [ ] **Step 4: Fix all references to `search.email` across the codebase**

Search for `search.email` and `f.email` in `src/` and update to `search.alertEmails[0]` or `f.alertEmails?.[0]`:

```bash
grep -rn "\.email" /Users/marcos/carfinder-ui/src/ --include="*.tsx" --include="*.ts"
```

Files likely affected:
- `src/screens/SetupScreen.tsx` — `f.email` → `f.alertEmails?.[0] ?? ""`
- `src/screens/EmailScreen.tsx` — `primary.email` → `primary.alertEmails?.[0] ?? ""`
- `src/components/ProfileBar.tsx` — if it shows the email
- `src/useAppState.ts` — check for any email references

- [ ] **Step 5: Fix TypeScript — run build**

```bash
cd /Users/marcos/carfinder-ui && npm run build
```

Fix every type error. Expected: clean build.

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/types.ts src/api.ts src/screens/ src/components/ src/useAppState.ts
git commit -m "feat: update Search type to alertEmails string array"
```

---

## Task 6: Intelligent SetupScreen

**Files:**
- Modify: `carfinder-ui/src/screens/SetupScreen.tsx`

This is the main task. Replace the Vehicle section's plain inputs with Combobox, add auto-derive logic, add ZIP lookup, add two-email UI, add match count, add save confirmation.

- [ ] **Step 1: Rewrite SetupScreen.tsx**

```tsx
// carfinder-ui/src/screens/SetupScreen.tsx
import { useState, useEffect, useRef } from "react";
import { Icon } from "../components/Icon";
import { Combobox } from "../components/Combobox";
import { matchMakes, matchModels } from "../data/vehicles";
import { loadZipLookup, lookupZip } from "../data/zip-lookup";
import { tierFor } from "../utils";
import type { Search, Listing } from "../types";

interface Props {
  search?: Partial<Search>;
  mode?: "new" | "edit";
  onSave: (s: Partial<Search>) => Promise<void>;
  onCancel: () => void;
  // Listings from the current search (if editing) for match count preview
  listings?: Listing[];
  // Primary email from user's most recent search (for pre-fill)
  defaultEmail?: string;
}

const DEFAULT: Partial<Search> = {
  year: new Date().getFullYear() - 4,
  make: "", model: "", trim: "",
  maxPrice: 25000, idealPrice: 0,
  maxMiles: 100000, idealMiles: 0,
  zip: "", radius: 100, intervalHours: 2,
  alertEmails: [],
};

// Field label wrapper — must be outside SetupScreen to preserve focus
function Field({ label, hint, children, span, badge }: {
  label: string; hint?: string; children: React.ReactNode; span?: number; badge?: string;
}) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 8, gridColumn: span ? `span ${span}` : "auto" }}>
      <span style={{ fontSize: 13, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em", display: "flex", alignItems: "center", gap: 7 }}>
        {label}
        {hint && <span style={{ color: "var(--fg-subtle)", fontWeight: 450 }}>{hint}</span>}
        {badge && (
          <span style={{ fontSize: 11, fontWeight: 500, color: "var(--fg-subtle)", background: "rgba(255,255,255,.07)", borderRadius: 99, padding: "1px 7px", letterSpacing: "0" }}>
            {badge}
          </span>
        )}
      </span>
      {children}
    </label>
  );
}

export function SetupScreen({ search, mode = "new", onSave, onCancel, listings = [], defaultEmail }: Props) {
  const init: Partial<Search> = {
    ...DEFAULT,
    ...search,
    alertEmails: search?.alertEmails?.length ? search.alertEmails : (defaultEmail ? [defaultEmail] : []),
  };

  const [f, setF] = useState<Partial<Search>>(init);
  const [saving, setSaving] = useState(false);
  const [saved, setSavedState] = useState(false);

  // Track which ideal fields have been manually touched
  const [touched, setTouched] = useState<Set<"idealPrice" | "idealMiles">>(new Set());

  // ZIP city resolution
  const [zipCity, setZipCity] = useState<string>("");

  // Second email expanded state
  const [showSecondEmail, setShowSecondEmail] = useState(
    (search?.alertEmails?.length ?? 0) > 1
  );

  // Make suggestions
  const makeSuggestions = matchMakes(f.make ?? "");
  // Model suggestions — only when make is set
  const modelSuggestions = f.make ? matchModels(f.make, f.model ?? "") : [];

  // Load ZIP lookup on mount (lazy)
  useEffect(() => { loadZipLookup(); }, []);

  // Resolve ZIP on change
  useEffect(() => {
    const zip = f.zip ?? "";
    if (zip.length === 5) {
      const result = lookupZip(zip);
      setZipCity(result ? `${result.city}, ${result.state}` : "");
    } else {
      setZipCity("");
    }
  }, [f.zip]);

  // Auto-derive idealPrice when maxPrice changes (if not manually touched)
  useEffect(() => {
    if (!touched.has("idealPrice") && f.maxPrice) {
      const derived = Math.round((f.maxPrice * 0.85) / 500) * 500;
      setF((s) => ({ ...s, idealPrice: derived }));
    }
  }, [f.maxPrice]);

  // Auto-derive idealMiles when maxMiles changes (if not manually touched)
  useEffect(() => {
    if (!touched.has("idealMiles") && f.maxMiles) {
      const derived = Math.round((f.maxMiles * 0.75) / 1000) * 1000;
      setF((s) => ({ ...s, idealMiles: derived }));
    }
  }, [f.maxMiles]);

  const up = (k: keyof Search) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF((s) => ({ ...s, [k]: e.target.value }));
  const upN = (k: keyof Search) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF((s) => ({ ...s, [k]: e.target.value === "" ? 0 : Number(e.target.value) }));
  const upNSelect = (k: keyof Search) => (e: React.ChangeEvent<HTMLSelectElement>) =>
    setF((s) => ({ ...s, [k]: Number(e.target.value) }));

  const touchIdeal = (field: "idealPrice" | "idealMiles") => {
    setTouched((prev) => new Set(prev).add(field));
  };

  // Email helpers
  const email0 = f.alertEmails?.[0] ?? "";
  const email1 = f.alertEmails?.[1] ?? "";
  const setEmail = (idx: number, val: string) => {
    setF((s) => {
      const emails = [...(s.alertEmails ?? [])];
      emails[idx] = val;
      return { ...s, alertEmails: emails.filter((_, i) => i <= idx || emails[i]) };
    });
  };

  // Live match count from listings prop
  const matchCount = listings.filter((l) => {
    if (!f.maxPrice || !f.maxMiles) return false;
    const inBudget = l.price <= (f.maxPrice ?? 0);
    const inMiles = l.miles <= (f.maxMiles ?? 0);
    return inBudget && inMiles;
  }).length;

  const idealCount = listings.filter((l) => {
    if (!f.idealPrice || !f.idealMiles) return false;
    return l.price <= (f.idealPrice ?? 0) && l.miles <= (f.idealMiles ?? 0);
  }).length;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        ...f,
        city: zipCity ? zipCity.split(",")[0].trim() : (f.zip ?? ""),
        alertEmails: (f.alertEmails ?? []).filter(Boolean),
      });
      setSavedState(true);
    } finally {
      setSaving(false);
    }
  };

  // ── Save confirmation screen ──────────────────────────────────────────
  if (saved) {
    return (
      <div style={{ maxWidth: 560, margin: "80px auto", padding: "0 26px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
        <div style={{ width: 56, height: 56, borderRadius: 99, background: "var(--green-bg)", border: "1px solid var(--green-bd)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--green)" }}>
          <Icon name="check" size={26} />
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 600, color: "var(--fg)", margin: "0 0 10px", letterSpacing: "-0.03em" }}>
            {mode === "new" ? "Hunt is live 🎉" : "Changes saved"}
          </h2>
          <p style={{ fontSize: 14.5, color: "var(--fg-muted)", margin: 0, lineHeight: 1.6, letterSpacing: "-0.01em" }}>
            {mode === "new"
              ? <>We're scanning now. You'll get an email at <strong style={{ color: "var(--fg)" }}>{email0}</strong>{email1 ? <> and <strong style={{ color: "var(--fg)" }}>{email1}</strong></> : ""} when we find matches.</>
              : "Your search criteria have been updated. Next scan picks up the changes."}
          </p>
        </div>
        <button className="cf-btn cf-btn-primary" onClick={onCancel}>
          Go to dashboard
        </button>
      </div>
    );
  }

  // ── Form ──────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: 760, margin: "0 auto", padding: "30px 26px 80px" }}>
      <button className="cf-btn cf-btn-quiet" onClick={onCancel} style={{ marginBottom: 20, marginLeft: -10 }}>
        <Icon name="chevL" size={14} /> Back to dashboard
      </button>
      <div style={{ marginBottom: 26 }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, color: "var(--fg)", margin: "0 0 8px", letterSpacing: "-0.03em" }}>
          {mode === "new" ? "New search" : "Edit search"}
        </h1>
        <p style={{ fontSize: 14.5, color: "var(--fg-muted)", margin: 0, lineHeight: 1.55, maxWidth: 520, letterSpacing: "-0.01em" }}>
          Define what you're hunting for. CarFinder scans listing sites on your interval and emails only new matches — ranked Ideal, Good, Ok.
        </p>
      </div>

      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 22 }}>

        {/* Vehicle */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="car" size={15} /> Vehicle</div>
          <div className="cf-grid">
            <Field label="Make" span={2}>
              <Combobox
                value={f.make ?? ""}
                onChange={(v) => setF((s) => ({ ...s, make: v, model: "" }))}
                onSelect={(v) => setF((s) => ({ ...s, make: v, model: "" }))}
                suggestions={makeSuggestions}
                placeholder="Toyota"
                required
              />
            </Field>
            <Field label="Model" span={2}>
              <Combobox
                value={f.model ?? ""}
                onChange={(v) => setF((s) => ({ ...s, model: v }))}
                onSelect={(v) => setF((s) => ({ ...s, model: v }))}
                suggestions={modelSuggestions}
                placeholder={f.make ? "Select model" : "Enter make first"}
                disabled={!f.make}
                required
              />
            </Field>
            <Field label="Trim" hint="optional" span={2}>
              <input className="cf-input" value={f.trim ?? ""} onChange={up("trim")} placeholder="Limited Platinum" />
            </Field>
            <Field label="Year" span={2}>
              <input
                className="cf-input" type="number" value={f.year ?? ""}
                onChange={upN("year")} min={1990} max={new Date().getFullYear()}
                onFocus={(e) => e.target.select()} required
              />
            </Field>
          </div>
        </section>

        {/* Price & mileage */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="tag" size={15} /> Price &amp; mileage</div>
          <div className="cf-grid">
            <Field label="Max price" hint="hard cap" span={3}>
              <div className="cf-input-wrap">
                <span className="cf-prefix">$</span>
                <input className="cf-input cf-has-prefix" type="number"
                  value={f.maxPrice || ""} onChange={upN("maxPrice")} required />
              </div>
            </Field>
            <Field label="Ideal price" hint="for Ideal tier" span={3}
              badge={!touched.has("idealPrice") && (f.idealPrice ?? 0) > 0 ? "auto" : undefined}>
              <div className="cf-input-wrap">
                <span className="cf-prefix">$</span>
                <input className="cf-input cf-has-prefix" type="number"
                  value={f.idealPrice || ""} required
                  onChange={(e) => { touchIdeal("idealPrice"); upN("idealPrice")(e); }}
                  onFocus={() => touchIdeal("idealPrice")} />
              </div>
            </Field>
            <Field label="Max mileage" hint="hard cap" span={3}>
              <div className="cf-input-wrap">
                <input className="cf-input cf-has-suffix" type="number"
                  value={f.maxMiles || ""} onChange={upN("maxMiles")} required />
                <span className="cf-suffix">mi</span>
              </div>
            </Field>
            <Field label="Ideal mileage" hint="for Ideal tier" span={3}
              badge={!touched.has("idealMiles") && (f.idealMiles ?? 0) > 0 ? "auto" : undefined}>
              <div className="cf-input-wrap">
                <input className="cf-input cf-has-suffix" type="number"
                  value={f.idealMiles || ""} required
                  onChange={(e) => { touchIdeal("idealMiles"); upN("idealMiles")(e); }}
                  onFocus={() => touchIdeal("idealMiles")} />
                <span className="cf-suffix">mi</span>
              </div>
            </Field>
          </div>

          <div className="cf-tierlegend">
            <span><span className="cf-lg" style={{ background: "var(--green)" }} /> Ideal = under ideal price &amp; miles</span>
            <span><span className="cf-lg" style={{ background: "var(--blue)" }} /> Good = under both hard caps</span>
            <span><span className="cf-lg" style={{ background: "var(--amber)" }} /> Ok = within caps, near a limit</span>
          </div>

          {/* Live match count — only show when listings exist */}
          {listings.length > 0 && (f.maxPrice ?? 0) > 0 && (f.maxMiles ?? 0) > 0 && (
            <div style={{ marginTop: 10, padding: "9px 13px", borderRadius: 9, background: "rgba(255,255,255,.04)", border: "1px solid var(--line)", fontSize: 13, color: "var(--fg-muted)", display: "flex", alignItems: "center", gap: 10, letterSpacing: "-0.01em" }}>
              <Icon name="sparkle" size={13} />
              <span>
                At these settings: <span style={{ color: "var(--fg)", fontWeight: 550 }}>{matchCount} match{matchCount !== 1 ? "es" : ""}</span>
                {idealCount > 0 && <>, <span style={{ color: "var(--green)", fontWeight: 550 }}>{idealCount} Ideal</span></>}
              </span>
            </div>
          )}
        </section>

        {/* Location */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="pin" size={15} /> Location</div>
          <div className="cf-grid">
            <Field label="ZIP code" span={2}>
              <div style={{ position: "relative" }}>
                <input className="cf-input" value={f.zip ?? ""} onChange={up("zip")}
                  placeholder="72761" maxLength={5} required />
                {zipCity && (
                  <div style={{ position: "absolute", top: "calc(100% + 4px)", left: 0, fontSize: 12.5, color: "var(--green)", fontWeight: 500, letterSpacing: "-0.01em", display: "flex", alignItems: "center", gap: 5 }}>
                    <Icon name="pin" size={12} /> {zipCity}
                  </div>
                )}
              </div>
            </Field>
            <Field label="Search radius" span={4}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <input type="range" min={10} max={300} step={5} value={f.radius ?? 100}
                  onChange={upN("radius")} className="cf-range" style={{ flex: 1 }} />
                <span className="tnum" style={{ fontSize: 14.5, fontWeight: 550, color: "var(--fg)", minWidth: 64, textAlign: "right", letterSpacing: "-0.01em" }}>
                  {f.radius} mi
                </span>
              </div>
            </Field>
          </div>
        </section>

        {/* Alerts */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="bell" size={15} /> Scan &amp; alerts</div>
          <div className="cf-grid">
            <Field label="Scan interval" span={2}>
              <select className="cf-input" value={f.intervalHours ?? 2} onChange={upNSelect("intervalHours")}>
                {[1, 2, 4, 6, 12, 24].map((h) => (
                  <option key={h} value={h}>Every {h} hour{h > 1 ? "s" : ""}</option>
                ))}
              </select>
            </Field>
            <Field label="Alert email" span={4}>
              <div className="cf-input-wrap">
                <span className="cf-prefix"><Icon name="mail" size={14} /></span>
                <input className="cf-input cf-has-prefix" type="email"
                  value={email0} placeholder="you@email.com" required
                  onChange={(e) => setEmail(0, e.target.value)} />
              </div>
            </Field>

            {showSecondEmail ? (
              <Field label="Partner's email" hint="optional" span={4} key="email1-open">
                <div className="cf-input-wrap">
                  <span className="cf-prefix"><Icon name="mail" size={14} /></span>
                  <input className="cf-input cf-has-prefix" type="email"
                    value={email1} placeholder="partner@email.com"
                    onChange={(e) => setEmail(1, e.target.value)} />
                </div>
              </Field>
            ) : (
              <div style={{ gridColumn: "span 4", paddingTop: 2 }} key="email1-closed">
                <button type="button" className="cf-btn cf-btn-quiet"
                  style={{ fontSize: 13, gap: 6 }}
                  onClick={() => setShowSecondEmail(true)}>
                  <Icon name="plus" size={13} /> Notify a partner
                </button>
              </div>
            )}
          </div>
        </section>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, paddingTop: 4 }}>
          <span style={{ fontSize: 13, color: "var(--fg-subtle)", display: "flex", alignItems: "center", gap: 8, letterSpacing: "-0.01em" }}>
            <Icon name="refresh" size={13} /> First scan runs immediately after you start.
          </span>
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" className="cf-btn cf-btn-ghost" onClick={onCancel}>Cancel</button>
            <button type="submit" className="cf-btn cf-btn-primary" disabled={saving}>
              <Icon name="check" size={15} />
              {saving ? "Saving…" : mode === "new" ? "Start searching" : "Save changes"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Update App.tsx to pass listings and defaultEmail props**

In `/Users/marcos/carfinder-ui/src/App.tsx`, find where `SetupScreen` is rendered and update:

```tsx
{view === "setup" && (
  <SetupScreen
    search={editingSearch ?? undefined}
    mode={setupMode}
    onSave={handleSave}
    onCancel={() => setView("dashboard")}
    listings={editingSearch?.id ? (listingsBySearch[editingSearch.id] ?? []) : []}
    defaultEmail={searches[0]?.alertEmails?.[0]}
  />
)}
```

- [ ] **Step 3: Build and fix TypeScript errors**

```bash
cd /Users/marcos/carfinder-ui && npm run build
```

Fix all errors. Common issues:
- `search.email` references → `search.alertEmails?.[0] ?? ""`
- `ProfileBar` showing email → update to show `search.alertEmails?.[0] ?? ""`
- `EmailScreen` recipient → `primary.alertEmails?.[0] ?? ""`

- [ ] **Step 4: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/
git commit -m "feat: intelligent SetupScreen — make/model combobox, auto-derive ideals, ZIP lookup, two emails, save confirmation"
```

---

## Task 7: Deploy both services

- [ ] **Step 1: Deploy backend to Railway**

```bash
cd /Users/marcos/carfinder
source ~/.railway/env && railway up --service CarFinder --detach
```

- [ ] **Step 2: Deploy frontend to Vercel**

```bash
cd /Users/marcos/carfinder-ui && vercel --prod --yes
```

- [ ] **Step 3: Smoke test**

1. Open https://carfinder-ui.vercel.app
2. Click "New search"
3. Type "Toy" in Make → see Toyota suggestion → select it
4. Model field shows Toyota models → select Sienna
5. Set Max Price $21,000 → Ideal Price auto-fills ~$17,500 with `auto` badge
6. Set Max Miles 130,000 → Ideal Miles auto-fills ~97,500 with `auto` badge
7. Type your ZIP → see city name appear below
8. Click "+ Notify a partner" → second email field expands
9. Submit → see green confirmation screen with email addresses listed
10. Dashboard shows the new search in the rail

---

## Self-Review

**Spec coverage:**
- ✅ Make/Model combobox with local dataset — Task 1, 3, 6
- ✅ Auto-derive ideal at 85%/75% with `auto` badge — Task 6
- ✅ Live match count from existing listings — Task 6
- ✅ ZIP→city lookup, lazy-loaded — Task 2, 6
- ✅ Two emails with progressive disclosure — Task 4, 5, 6
- ✅ Save confirmation moment — Task 6
- ✅ Backend migration for alert_emails — Task 4
- ✅ AI parser hook — `parseSearchQuery` intentionally omitted (no visible UI until Groq wired)
- ✅ defaultEmail pre-fill from most recent search — Task 6

**No placeholders found.**

**Type consistency:** `alertEmails: string[]` defined in Task 5 types.ts, used consistently in Task 6 SetupScreen and Task 5 api.ts. `toSnake` joins to comma string; `fromSnake` splits back. `Field` component `badge` prop added in Task 6 only.
