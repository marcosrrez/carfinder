# Trim & Drivetrain Selection Design

**Date:** 2026-06-06  
**Status:** Approved for implementation

---

## Goal

Let users specify exactly which trims and drivetrain they want for a given search. The scanner only surfaces listings that match — no more sifting through base LE trims when you specifically want XLE AWD.

---

## Context

Currently `trim` is a free-text string field stored in the DB but never used by the scanner or scorer. This feature replaces it with a multi-select trim picker backed by a curated dataset, wires the selection into Marketcheck filtering, and adds a drivetrain (AWD/FWD/4WD/RWD) AND-filter.

---

## Data Structure

### New file: `carfinder-ui/src/data/trim-data.ts`

Lazy-loaded (dynamic import on model selection), separate from `vehicles.ts` to keep bundle size small.

```ts
export interface TrimOption {
  name: string;           // "XLE", "Limited", "Platinum"
  description: string;   // One sentence: what it adds, who it's for
  drivetrains: Drivetrain[];  // Which drivetrains are available for this trim
  badge?: string;         // "Most popular" | "Best value" | "Top of line"
}

export type Drivetrain = "FWD" | "AWD" | "4WD" | "RWD";

export interface ModelTrims {
  make: string;
  model: string;
  yearRange?: string;     // "2014–2019" — when trims differ by generation
  trims: TrimOption[];
}
```

The dataset covers every model in `vehicles.ts` — approximately 150 entries, written by hand with accurate trim names, descriptions, and drivetrain availability. Example:

```ts
{
  make: "Toyota",
  model: "Highlander",
  yearRange: "2014–2019",
  trims: [
    { name: "LE", description: "Base trim with 8-inch display, Toyota Safety Sense, and three-row seating.", drivetrains: ["FWD", "AWD"] },
    { name: "LE Plus", description: "Adds power liftgate and SofTex seating over LE — dropped after 2019.", drivetrains: ["FWD", "AWD"] },
    { name: "XLE", description: "The sweet spot: dual-zone climate, power liftgate, sunroof, heated front seats. Most popular trim.", drivetrains: ["FWD", "AWD"], badge: "Most popular" },
    { name: "XLE Premium", description: "Adds ventilated front seats and a larger 8-inch audio upgrade over XLE.", drivetrains: ["FWD", "AWD"] },
    { name: "Limited", description: "Leather interior, navigation, 20-inch wheels, bird's-eye view camera.", drivetrains: ["FWD", "AWD"] },
    { name: "Limited Platinum", description: "Top of the line: heated/ventilated second row, premium JBL audio, panoramic roof.", drivetrains: ["AWD"], badge: "Top of line" },
  ]
}
```

Notable year-specific notes are embedded in descriptions (e.g. "2016 refined the 3.5L V6 reliability over the 2014–2015 launch models").

### Lookup helpers

```ts
export function getTrims(make: string, model: string): TrimOption[]
// Returns trims for the make/model combo. Returns [] if not in dataset.

export async function loadTrimData(): Promise<void>
// Dynamic import — call once on model selection, subsequent calls are no-ops.
```

---

## Search Type Changes

### `types.ts`

```ts
export type Drivetrain = "FWD" | "AWD" | "4WD" | "RWD";

export interface Search {
  // ... existing fields ...
  trims: string[];          // was: trim: string
  drivetrain: Drivetrain | "Any";  // global drivetrain AND-filter
}
```

### `api.ts` — toSnake

```ts
trims:      (s.trims ?? []).join(","),   // stored as comma-separated (trim names have no commas)
drivetrain: s.drivetrain ?? "Any",
```

### `api.ts` — fromSnake

```ts
trims:      ((r.trims ?? r.trim ?? "") as string).split(",").map(s => s.trim()).filter(Boolean),
drivetrain: (r.drivetrain ?? "Any") as Drivetrain | "Any",
```

---

## Database Changes

### `models.py`

Add two columns to `searches`:

```sql
trims      TEXT NOT NULL DEFAULT ''
drivetrain TEXT NOT NULL DEFAULT 'Any'
```

Migration block (safe for existing DBs):

```python
for col, default in [("trims", "''"), ("drivetrain", "'Any'")]:
    try:
        self.conn.execute(f"ALTER TABLE searches ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        self.conn.commit()
    except Exception:
        pass
```

Migrate existing `trim` data: `UPDATE searches SET trims = trim WHERE trims = '' AND trim != ''`

### `api/searches.py`

- Remove `trim` from `required` list (it was never required anyway, just defaulted to `""`)
- Add `trims` and `drivetrain` to allowed update fields

---

## Scanner Changes

### Marketcheck filtering

Marketcheck's `/search` endpoint accepts `trim` as a query param (exact match). For OR logic across multiple trims, we make one request per selected trim and deduplicate by listing ID — or use the `trim` param with comma-separation if the API supports it (verify at implementation time).

If `trims` is empty: no trim filter applied (returns all trims).

Drivetrain filter: Marketcheck supports `drivetrain` param. Pass it when `drivetrain !== "Any"`. This is an AND on top of trim filtering.

---

## Scorer Changes

### `scorer.py`

Add a trim match bonus to the scoring function:

```python
def score(listing, search):
    # ... existing price/mileage scoring ...
    
    # Trim bonus: +10 points if listing trim matches a selected trim
    if search.get("trims"):
        selected = [t.lower() for t in search["trims"]]
        listing_trim = (listing.get("trim") or "").lower()
        if any(t in listing_trim for t in selected):
            score += 10
    
    return score
```

The bonus nudges matched trims toward Ideal without hard-excluding non-matched trims from the display (the scanner filter handles exclusion).

---

## UI Design

### Trim selector in SetupScreen

Appears **inline below the Model field** after a model is selected and trim data loads. No page change, no modal.

```
┌─ Vehicle ──────────────────────────────────────────────┐
│  Make: [Toyota ▾]   Model: [Highlander ▾]              │
│  Year: [2016   ]    Trim: ─────────────────────────── │
│                                                        │
│  Drivetrain  ○ Any  ○ FWD  ● AWD  ○ 4WD               │
│                                                        │
│  Trims  [Any trim ×]  ← active when nothing selected  │
│                                                        │
│  ☑ XLE          AWD · FWD                             │
│    The sweet spot: dual-zone climate, sunroof,         │
│    heated front seats. Most popular trim.  ★ Popular   │
│                                                        │
│  ☑ Limited      AWD · FWD                             │
│    Leather, navigation, 20-inch wheels,                │
│    bird's-eye view camera.                             │
│                                                        │
│  ☐ LE           AWD · FWD                             │
│    Base trim with 8-inch display and Safety Sense.     │
│                                                        │
│  ☐ Limited Platinum  AWD only                         │
│    Top of line: heated/ventilated second row,          │
│    panoramic roof.  ★ Top of line                      │
│                                                        │
│  Trim: [Limited Platinum] ← free-text fallback        │
│  (for makes/models not in our dataset)                 │
└────────────────────────────────────────────────────────┘
```

### Interaction rules

- **Drivetrain selector** (Any/FWD/AWD/4WD/RWD) — radio buttons, shown above trim list. Acts as AND filter. Trims incompatible with the selected drivetrain are visually dimmed but still selectable (with a note: "not available in AWD").
- **"Any trim" chip** — active by default when nothing is selected. Disappears when a trim is checked. Clicking it clears all selections. Makes the "I haven't narrowed yet" state explicit and intentional.
- **Trim checkboxes** — full-width rows, description always visible (no expand/collapse — users should read them). Badge ("Most popular") shown as a small pill.
- **Free-text fallback** — if the model isn't in our dataset, the trim selector is hidden and the original plain text input is shown.
- **Loading state** — trim data is lazy-loaded on model selection. Show a brief skeleton (2–3 placeholder rows) while loading. In practice this is <100ms since it's a local file, but the skeleton prevents layout jump.

---

## What Doesn't Change

- Dashboard listing cards — they already show trim from Marketcheck data
- Email alerts — they already include trim in listing details
- The `Listing` type — already has `trim: string` from the API

---

## Out of Scope

- Year-aware trim filtering (e.g., "XLE was different in 2014 vs 2016") — descriptions note differences, but the filter just matches on name
- Trim exclusion (NOT XLE) — not needed, users select what they want
- Custom trim names not in our dataset — handled by free-text fallback
