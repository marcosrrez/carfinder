# CarFinder Plan B — React Frontend SPA

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished React SPA that matches the design handoff exactly — Dashboard, Setup, Email, and Compare views — wired to the Plan A backend API.

**Architecture:** Vite + React + TypeScript. All state lives in a single `useAppState` hook that fetches from the backend REST API (`VITE_API_URL`). CSS custom properties carry design tokens; no UI framework. Components mirror the design handoff's component tree: `ListingCard`, `TopPick`, `DealGauge`, `SetupScreen`, `EmailScreen`, `CompareModal`. Deploy to Vercel.

**Tech Stack:** Vite 5, React 18, TypeScript 5, CSS Modules (one global `tokens.css`), Onest font (Google Fonts), Vercel CLI

---

## File Structure

```
carfinder-ui/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── .env.example              # VITE_API_URL=http://localhost:5000
├── .env.local                # (gitignored) VITE_API_URL=https://...railway.app
├── src/
│   ├── main.tsx              # ReactDOM.createRoot
│   ├── App.tsx               # Router: Dashboard / Setup / Email / Compare
│   ├── tokens.css            # CSS custom properties + global resets
│   ├── types.ts              # Listing, Search, Deal, Tier TypeScript types
│   ├── api.ts                # fetch wrappers for all backend endpoints
│   ├── utils.ts              # fmtPrice, fmtMiles, fmtDelta, tierFor, dealFor
│   ├── useAppState.ts        # single top-level hook: fetches + mutations
│   ├── components/
│   │   ├── Icon.tsx          # SVG icon registry (all icons used in design)
│   │   ├── TopBar.tsx        # sticky nav with search tabs + new-count badge
│   │   ├── StatCard.tsx      # stat surface tile
│   │   ├── TierBadge.tsx     # colored dot / badge for ideal/good/ok
│   │   ├── DealSignal.tsx    # compact one-line deal label
│   │   ├── DealGauge.tsx     # expanded gauge bar
│   │   ├── SpecCell.tsx      # icon + label + value spec grid cell
│   │   ├── Collapse.tsx      # CSS animate-in/out expand panel
│   │   ├── ListingDetail.tsx # full expanded content inside a card
│   │   ├── ListingCard.tsx   # collapsed + expandable listing row
│   │   ├── TopPick.tsx       # top-pick callout card
│   │   ├── ProfileBar.tsx    # active search summary bar
│   │   ├── AllSummary.tsx    # multi-search overview tiles
│   │   └── ScanFooter.tsx    # sticky scan-now footer bar
│   ├── screens/
│   │   ├── Dashboard.tsx     # main listing view with filters
│   │   ├── SetupScreen.tsx   # new/edit search form
│   │   ├── EmailScreen.tsx   # email alert preview
│   │   └── CompareModal.tsx  # side-by-side saved listings
│   └── vite-env.d.ts
├── vercel.json               # SPA rewrite rule
└── package.json
```

---

## Task 1: Scaffold Vite project

**Files:**
- Create: `carfinder-ui/` (entire project root)
- Create: `carfinder-ui/package.json`
- Create: `carfinder-ui/vite.config.ts`
- Create: `carfinder-ui/tsconfig.json`
- Create: `carfinder-ui/index.html`
- Create: `carfinder-ui/.env.example`
- Create: `carfinder-ui/vercel.json`

- [ ] **Step 1: Create the project directory and package.json**

```bash
mkdir -p /Users/marcos/carfinder-ui
cd /Users/marcos/carfinder-ui
```

Create `package.json`:

```json
{
  "name": "carfinder-ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.3.4"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CarFinder</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;450;500;550;600;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create .env.example**

```
VITE_API_URL=http://localhost:5000
VITE_USER_ID=user_dev
```

- [ ] **Step 6: Create vercel.json**

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [ ] **Step 7: Install dependencies**

```bash
cd /Users/marcos/carfinder-ui && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 8: Create src/vite-env.d.ts**

```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_USER_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

- [ ] **Step 9: Commit**

```bash
cd /Users/marcos/carfinder-ui
git init && git add .
git commit -m "feat: scaffold vite+react+ts project"
```

---

## Task 2: Design tokens, global CSS, and types

**Files:**
- Create: `src/tokens.css`
- Create: `src/types.ts`

- [ ] **Step 1: Create src/tokens.css**

```css
/* ── Google Font is loaded in index.html ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:         #0a0b0d;
  --surface:    #101216;
  --surface-2:  #13161b;
  --line:       rgba(255,255,255,.07);
  --line-2:     rgba(255,255,255,.11);
  --chip:       rgba(255,255,255,.06);
  --fg:         #f0f0f2;
  --fg-muted:   #8b8d96;
  --fg-subtle:  #555760;

  /* Accent colors */
  --accent:     #4f8ff5;
  --green:      #6ec594;
  --blue:       #7aa2f0;
  --amber:      #d6ad6a;

  /* Tier backgrounds / borders */
  --green-bg:   rgba(110,197,148,.08);
  --green-bd:   rgba(110,197,148,.18);
  --blue-bg:    rgba(122,162,240,.08);
  --blue-bd:    rgba(122,162,240,.18);
  --amber-bg:   rgba(214,173,106,.08);
  --amber-bd:   rgba(214,173,106,.18);
}

html, body, #root {
  height: 100%;
  background: var(--bg);
  color: var(--fg);
  font-family: "Onest", system-ui, sans-serif;
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}

/* Tabular nums helper */
.tnum { font-variant-numeric: tabular-nums; }

/* ── Buttons ── */
.cf-btn {
  display: inline-flex; align-items: center; gap: 6px;
  height: 36px; padding: 0 14px; border-radius: 9px;
  font-family: inherit; font-size: 13.5px; font-weight: 550;
  letter-spacing: -0.01em; cursor: pointer; border: none;
  transition: opacity .15s, background .15s, color .15s, border-color .15s;
  text-decoration: none;
}
.cf-btn:disabled { opacity: .45; cursor: not-allowed; }
.cf-btn-primary  { background: var(--accent); color: #fff; }
.cf-btn-primary:hover:not(:disabled) { opacity: .88; }
.cf-btn-ghost    { background: transparent; color: var(--fg-muted);
                   border: 1px solid var(--line-2); }
.cf-btn-ghost:hover { color: var(--fg); border-color: var(--line-2); background: rgba(255,255,255,.04); }
.cf-btn-quiet    { background: transparent; color: var(--fg-muted); border: none; padding: 0 6px; }
.cf-btn-quiet:hover { color: var(--fg); }

/* ── Icon button ── */
.cf-iconbtn {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; cursor: pointer;
  color: var(--fg-subtle); font-size: 0; transition: color .15s, background .15s;
}
.cf-iconbtn:hover { color: var(--fg); background: rgba(255,255,255,.05); }

/* ── Link button ── */
.cf-linkbtn {
  background: none; border: none; cursor: pointer;
  font: inherit; font-size: 13px; color: var(--fg-subtle);
  text-decoration: underline; text-underline-offset: 3px;
}
.cf-linkbtn:hover { color: var(--fg); }

/* ── Nav tabs ── */
.cf-tab {
  display: inline-flex; align-items: center; gap: 6px;
  height: 30px; padding: 0 11px; border-radius: 7px;
  font-family: inherit; font-size: 13.5px; font-weight: 500;
  letter-spacing: -0.01em; cursor: pointer;
  background: transparent; border: none;
  color: var(--fg-muted); transition: color .15s, background .15s;
}
.cf-tab:hover { color: var(--fg); background: rgba(255,255,255,.05); }
.cf-tab[data-active="true"] { color: var(--fg); background: rgba(255,255,255,.08); }

.cf-tab-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  border-radius: 99px; background: var(--accent);
  font-size: 11px; font-weight: 600; color: #fff;
}

/* ── Filter pills ── */
.cf-filter {
  display: inline-flex; align-items: center; gap: 5px;
  height: 30px; padding: 0 10px; border-radius: 7px;
  font-family: inherit; font-size: 13px; font-weight: 500;
  letter-spacing: -0.01em; cursor: pointer;
  background: transparent; border: none;
  color: var(--fg-muted); transition: color .15s, background .15s;
}
.cf-filter:hover { color: var(--fg); background: rgba(255,255,255,.05); }
.cf-filter[data-active="true"] { color: var(--fg); background: rgba(255,255,255,.08); }
.cf-fdot {
  width: 7px; height: 7px; border-radius: 99px;
  background: var(--fdot, var(--fg-subtle));
  flex: none;
}

/* ── Cards ── */
.cf-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  transition: border-color .15s;
}
.cf-listing { cursor: default; }
.cf-listing:hover { border-color: var(--line-2); }

/* Subtle left-accent bar variant — rendered by ListingCard */
.cf-listing-actions { opacity: 0; transition: opacity .15s; }
.cf-listing:hover .cf-listing-actions { opacity: 1; }

/* Expand chevron rotation */
.cf-chev svg { transition: transform .2s; }
.cf-chev[data-open="true"] svg { transform: rotate(180deg); }

/* ── Collapse animation ── */
@keyframes cf-open { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:translateY(0); } }
@keyframes cf-close { from { opacity:1; transform:translateY(0); } to { opacity:0; transform:translateY(-6px); } }
.cf-collapse[data-open="true"]  { animation: cf-open  .2s ease forwards; }
.cf-collapse[data-open="false"] { animation: cf-close .22s ease forwards; }

/* ── Rise animation (staggered list) ── */
@keyframes cf-rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.cf-rise { animation: cf-rise .25s ease both; }

/* ── Spin + breathe ── */
@keyframes cf-spin   { to { transform: rotate(360deg); } }
@keyframes cf-breath { 0%,100%{opacity:1} 50%{opacity:.6} }
.cf-spin   { animation: cf-spin 1s linear infinite; display: inline-flex; }
.cf-breath { animation: cf-breath 1.8s ease-in-out infinite; }

/* ── Form elements ── */
.cf-form-sec { padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.cf-form-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: var(--fg-muted);
  letter-spacing: -0.01em; text-transform: uppercase;
}
.cf-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }
.cf-input {
  width: 100%; height: 38px; padding: 0 12px;
  background: var(--surface-2); border: 1px solid var(--line-2);
  border-radius: 9px; color: var(--fg);
  font-family: inherit; font-size: 14px;
  transition: border-color .15s;
  -webkit-appearance: none;
}
.cf-input:focus { outline: none; border-color: var(--accent); }
.cf-input-wrap { position: relative; display: flex; align-items: center; }
.cf-prefix, .cf-suffix {
  position: absolute; font-size: 13.5px; color: var(--fg-muted); pointer-events: none;
}
.cf-prefix { left: 11px; }
.cf-suffix { right: 11px; }
.cf-has-prefix { padding-left: 24px; }
.cf-has-suffix { padding-right: 28px; }
.cf-range { width: 100%; accent-color: var(--accent); cursor: pointer; }

.cf-tierlegend {
  display: flex; gap: 20px; flex-wrap: wrap;
  font-size: 12px; color: var(--fg-subtle);
}
.cf-lg { display: inline-block; width: 8px; height: 8px; border-radius: 99px; margin-right: 5px; }

/* ── Stat card ── */
.cf-stat {
  flex: 1; padding: 16px 18px;
  display: flex; flex-direction: column; gap: 7px;
}

/* ── Compare nudge banner ── */
.cf-compare-nudge {
  display: flex; align-items: center; justify-content: space-between;
  padding: 13px 18px; border-radius: 12px;
  background: rgba(79,143,245,.07);
  border: 1px solid rgba(79,143,245,.18);
  cursor: pointer; width: 100%;
  font: inherit; font-size: 14px; color: var(--fg-muted);
  transition: background .15s;
}
.cf-compare-nudge:hover { background: rgba(79,143,245,.12); }

/* ── Search selector sidebar ── */
.cf-search-pill {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 14px; border-radius: 10px; cursor: pointer;
  border: none; width: 100%; text-align: left;
  background: transparent; font-family: inherit;
  transition: background .15s;
}
.cf-search-pill:hover { background: rgba(255,255,255,.04); }
.cf-search-pill[data-active="true"] { background: rgba(255,255,255,.07); }

/* ── Compare modal ── */
.cf-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,.72); backdrop-filter: blur(4px);
  display: flex; align-items: flex-start; justify-content: center;
  padding: 40px 20px; overflow-y: auto;
}
.cf-modal {
  background: var(--surface); border: 1px solid var(--line-2);
  border-radius: 16px; width: 100%; max-width: 1100px;
  padding: 28px 24px;
}
```

- [ ] **Step 2: Create src/types.ts**

```ts
export interface Seller {
  type: "Dealer" | "Private";
  name: string;
  rating: number | null;
}

export interface Drop {
  amount: number;
  when: string;
}

export interface Listing {
  id: string;
  title: string;
  price: number;
  miles: number;
  city: string;
  distance: number;
  source: string;
  url: string;
  posted: string;
  isNew: boolean;
  market: number;
  drivetrain: string;
  ext: string;
  int: string;
  owners: number;
  accidents: number;
  daysListed: number;
  photos: number;
  seller: Seller;
  vin: string;
  drop: Drop | null;
}

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
  email: string;
  active: boolean;
}

export type TierKey = "ideal" | "good" | "ok";
export type DealKey = "great" | "good" | "fair" | "high";

export interface Deal {
  key: DealKey;
  label: string;
  delta: number;
}

export interface EnrichedListing extends Listing {
  tier: TierKey;
  deal: Deal;
  searchId: string;
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/tokens.css src/types.ts
git commit -m "feat: add design tokens CSS and TypeScript types"
```

---

## Task 3: API client and utility functions

**Files:**
- Create: `src/api.ts`
- Create: `src/utils.ts`

- [ ] **Step 1: Create src/utils.ts**

```ts
import type { Listing, Search, TierKey, DealKey, Deal } from "./types";

export const fmtPrice = (n: number) =>
  "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });

export const fmtMiles = (n: number) =>
  n.toLocaleString("en-US") + " mi";

export const fmtDelta = (d: number) => {
  const abs = Math.abs(d);
  return (d < 0 ? "-" : "+") + fmtPrice(abs);
};

export function tierFor(listing: Listing, search: Search): TierKey {
  const cheap = listing.price <= search.idealPrice;
  const lowMi = listing.miles <= search.idealMiles;
  const inBudget = listing.price <= search.maxPrice;
  const inMiles = listing.miles <= search.maxMiles;
  if (cheap && lowMi) return "ideal";
  if (inBudget && inMiles) {
    const nearPrice = listing.price > search.maxPrice * 0.92;
    const nearMiles = listing.miles > search.maxMiles * 0.92;
    if (nearPrice || nearMiles) return "ok";
    return "good";
  }
  return "ok";
}

export function dealFor(listing: Listing): Deal {
  const d = listing.price - listing.market;
  if (d <= -1200) return { key: "great", label: "Great deal", delta: d };
  if (d <= -300)  return { key: "good",  label: "Good price", delta: d };
  if (d <= 600)   return { key: "fair",  label: "Fair price", delta: d };
  return { key: "high", label: "Above market", delta: d };
}

export const TIERS: Record<TierKey, { label: string; color: string; bg: string; border: string; desc: string }> = {
  ideal: { label: "Ideal", color: "var(--green)", bg: "var(--green-bg)", border: "var(--green-bd)", desc: "under both ideal price and mileage targets" },
  good:  { label: "Good",  color: "var(--blue)",  bg: "var(--blue-bg)",  border: "var(--blue-bd)",  desc: "within both hard caps" },
  ok:    { label: "Ok",    color: "var(--amber)", bg: "var(--amber-bg)", border: "var(--amber-bd)", desc: "near one of your limits" },
};

export const DEALS: Record<DealKey, { color: string }> = {
  great: { color: "var(--green)" },
  good:  { color: "var(--green)" },
  fair:  { color: "var(--fg-muted)" },
  high:  { color: "var(--amber)" },
};
```

- [ ] **Step 2: Create src/api.ts**

```ts
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";
const USER = import.meta.env.VITE_USER_ID ?? "user_dev";

const headers = () => ({
  "Content-Type": "application/json",
  "X-User-Id": USER,
});

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
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
};
```

- [ ] **Step 3: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/api.ts src/utils.ts
git commit -m "feat: add API client and utility functions"
```

---

## Task 4: Icon component and shared primitives

**Files:**
- Create: `src/components/Icon.tsx`
- Create: `src/components/TierBadge.tsx`
- Create: `src/components/DealSignal.tsx`
- Create: `src/components/StatCard.tsx`
- Create: `src/components/Collapse.tsx`

- [ ] **Step 1: Create src/components/Icon.tsx**

```tsx
const paths: Record<string, string> = {
  car:        "M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2M1 10l2-6h18l2 6M1 10h22v6H1zM6 16a1 1 0 1 0 0-2 1 1 0 0 0 0 2zM18 16a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
  tag:        "M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01",
  sparkle:    "M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z",
  star:       "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z",
  starFill:   "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z",
  refresh:    "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
  clock:      "M12 22c5.52 0 10-4.48 10-10S17.52 2 12 2 2 6.48 2 12s4.48 10 10 10zM12 6v6l4 2",
  bolt:       "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  trendDown:  "M23 18l-9.5-9.5-5 5L1 6M17 18h6v-6",
  shield:     "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  columns:    "M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18",
  pin:        "M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0zM12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  user:       "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  palette:    "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8z",
  calendar:   "M3 9h18M3 4h18v17H3zM16 2v4M8 2v4",
  gauge:      "M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm0 0v-4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83",
  drive:      "M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2h-3m-9 0a2 2 0 1 0 4 0 2 2 0 0 0-4 0zm9 0a2 2 0 1 0 4 0 2 2 0 0 0-4 0z",
  image:      "M21 19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4l2-3h4l2 3h4a2 2 0 0 1 2 2zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  arrowUpRight: "M7 17L17 7M7 7h10v10",
  chevD:      "M6 9l6 6 6-6",
  chevL:      "M15 18l-6-6 6-6",
  eyeOff:     "M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22",
  plus:       "M12 5v14M5 12h14",
  trash:      "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
  check:      "M20 6L9 17l-5-5",
  mail:       "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6",
};

interface IconProps {
  name: keyof typeof paths;
  size?: number;
  color?: string;
  fill?: string;
}

export function Icon({ name, size = 16, color = "currentColor", fill = "none" }: IconProps) {
  const d = paths[name];
  if (!d) return null;
  const isFilled = name === "starFill" || name === "bolt";
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill={isFilled ? color : fill}
      stroke={color} strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ display: "block", flex: "none" }}
    >
      <path d={d} />
    </svg>
  );
}
```

- [ ] **Step 2: Create src/components/TierBadge.tsx**

```tsx
import { TIERS } from "../utils";
import type { TierKey } from "../types";

interface Props { tier: TierKey; variant?: "dot" | "badge"; }

export function TierBadge({ tier, variant = "dot" }: Props) {
  const t = TIERS[tier];
  if (variant === "badge") {
    return (
      <span style={{
        display: "inline-flex", alignItems: "center", gap: 5,
        padding: "2px 9px", borderRadius: 99,
        background: t.bg, border: `1px solid ${t.border}`,
        fontSize: 11.5, fontWeight: 600, color: t.color, letterSpacing: "-0.01em",
      }}>
        {t.label}
      </span>
    );
  }
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12.5, fontWeight: 550, color: t.color }}>
      <span style={{ width: 7, height: 7, borderRadius: 99, background: t.color, flex: "none" }} />
      {t.label}
    </span>
  );
}
```

- [ ] **Step 3: Create src/components/DealSignal.tsx**

```tsx
import { DEALS, fmtDelta } from "../utils";
import { Icon } from "./Icon";
import type { Deal } from "../types";

export function DealSignal({ deal }: { deal: Deal }) {
  const d = DEALS[deal.key];
  const hasArrow = deal.key === "great" || deal.key === "good";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      fontSize: 12.5, fontWeight: 500, color: d.color,
      letterSpacing: "-0.01em", whiteSpace: "nowrap",
    }}>
      {hasArrow
        ? <Icon name="trendDown" size={13} />
        : <span style={{ width: 5, height: 5, borderRadius: 99, background: d.color }} />}
      {deal.label}
      {deal.delta < 0 && (
        <span style={{ color: "var(--fg-subtle)", fontWeight: 450 }}>{fmtDelta(deal.delta)}</span>
      )}
    </span>
  );
}
```

- [ ] **Step 4: Create src/components/StatCard.tsx**

```tsx
import { Icon } from "./Icon";

interface Props {
  label: string;
  value: string | number;
  sub: string;
  icon: Parameters<typeof Icon>[0]["name"];
}

export function StatCard({ label, value, sub, icon }: Props) {
  return (
    <div className="cf-card cf-stat">
      <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12.5, fontWeight: 500, color: "var(--fg-muted)", letterSpacing: "-0.01em" }}>
        <Icon name={icon} size={13} /> {label}
      </div>
      <div className="tnum" style={{ fontSize: 26, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.03em", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 12.5, color: "var(--fg-subtle)", letterSpacing: "-0.01em" }}>{sub}</div>
    </div>
  );
}
```

- [ ] **Step 5: Create src/components/Collapse.tsx**

```tsx
import { useState, useEffect, type ReactNode } from "react";

export function Collapse({ open, children }: { open: boolean; children: ReactNode }) {
  const [render, setRender] = useState(open);

  useEffect(() => {
    if (open) { setRender(true); return; }
    const id = setTimeout(() => setRender(false), 240);
    return () => clearTimeout(id);
  }, [open]);

  if (!render && !open) return null;
  return <div className="cf-collapse" data-open={open}>{children}</div>;
}
```

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/components/
git commit -m "feat: add Icon, TierBadge, DealSignal, StatCard, Collapse components"
```

---

## Task 5: Listing components (DealGauge, SpecCell, ListingDetail, ListingCard, TopPick)

**Files:**
- Create: `src/components/DealGauge.tsx`
- Create: `src/components/SpecCell.tsx`
- Create: `src/components/ListingDetail.tsx`
- Create: `src/components/ListingCard.tsx`
- Create: `src/components/TopPick.tsx`

- [ ] **Step 1: Create src/components/DealGauge.tsx**

```tsx
import { DEALS, fmtPrice, fmtDelta } from "../utils";
import { Icon } from "./Icon";
import type { Listing, Deal } from "../types";

export function DealGauge({ listing, deal }: { listing: Listing; deal: Deal }) {
  const d = DEALS[deal.key];
  const lo = listing.market * 0.85, hi = listing.market * 1.15;
  const pct = Math.max(4, Math.min(96, ((listing.price - lo) / (hi - lo)) * 100));
  const mkt = ((listing.market - lo) / (hi - lo)) * 100;
  const hasArrow = deal.key === "great" || deal.key === "good";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 7, fontSize: 13.5, fontWeight: 550, color: d.color, letterSpacing: "-0.01em", whiteSpace: "nowrap" }}>
          {hasArrow ? <Icon name="trendDown" size={15} /> : <Icon name="tag" size={14} />}
          {deal.label}
        </span>
        <span className="tnum" style={{ fontSize: 12.5, color: "var(--fg-muted)" }}>
          {deal.delta < 0 ? `${fmtDelta(deal.delta)} under` : deal.delta === 0 ? "at" : `${fmtDelta(deal.delta)} over`}{" "}
          market est. <span style={{ color: "var(--fg)" }}>{fmtPrice(listing.market)}</span>
        </span>
      </div>
      <div style={{ position: "relative", height: 6, borderRadius: 99, background: "linear-gradient(90deg, var(--green-bg), rgba(255,255,255,.05), var(--amber-bg))", boxShadow: "inset 0 0 0 1px var(--line)" }}>
        <span style={{ position: "absolute", top: -3, bottom: -3, left: `${mkt}%`, width: 1.5, background: "var(--fg-subtle)", transform: "translateX(-50%)", opacity: 0.6 }} />
        <span style={{ position: "absolute", top: "50%", left: `${pct}%`, width: 13, height: 13, borderRadius: 99, background: d.color, transform: "translate(-50%,-50%)", boxShadow: "0 0 0 3px var(--surface), 0 1px 4px rgba(0,0,0,.5)" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--fg-subtle)" }}>
        <span className="tnum">{fmtPrice(Math.round(lo))}</span>
        <span>market value</span>
        <span className="tnum">{fmtPrice(Math.round(hi))}</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create src/components/SpecCell.tsx**

```tsx
import { Icon } from "./Icon";

interface Props {
  icon: Parameters<typeof Icon>[0]["name"];
  label: string;
  value: string | number;
  accent?: string;
}

export function SpecCell({ icon, label, value, accent }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11.5, color: "var(--fg-subtle)", fontWeight: 500, letterSpacing: "-0.005em" }}>
        <Icon name={icon} size={13} /> {label}
      </span>
      <span className="tnum" style={{ fontSize: 13.5, fontWeight: 550, color: accent ?? "var(--fg)", letterSpacing: "-0.01em" }}>
        {value}
      </span>
    </div>
  );
}
```

- [ ] **Step 3: Create src/components/ListingDetail.tsx**

```tsx
import { TIERS, fmtPrice, fmtMiles } from "../utils";
import { Icon } from "./Icon";
import { DealGauge } from "./DealGauge";
import { SpecCell } from "./SpecCell";
import type { Listing, Search, TierKey, Deal } from "../types";

interface Props {
  listing: Listing;
  tier: TierKey;
  deal: Deal;
  search: Search;
  saved: boolean;
  onSave: () => void;
  onHide: () => void;
}

export function ListingDetail({ listing, tier, deal, search, saved, onSave, onHide }: Props) {
  const t = TIERS[tier];
  const age = new Date().getFullYear() - search.year || 1;
  const milesPerYear = Math.round(listing.miles / age);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, padding: "18px 20px 20px", borderTop: "1px solid var(--line)" }}>
      <DealGauge listing={listing} deal={deal} />

      {/* tier explanation */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 9, padding: "11px 13px", borderRadius: 11, background: t.bg, border: `1px solid ${t.border}` }}>
        <span style={{ color: t.color, display: "flex", marginTop: 1 }}><Icon name="shield" size={15} /></span>
        <span style={{ fontSize: 13, color: "var(--fg-muted)", lineHeight: 1.5, letterSpacing: "-0.01em" }}>
          Ranked <span style={{ color: t.color, fontWeight: 600 }}>{t.label}</span> — {t.desc}.
          {tier === "ideal" && <> Under your ideal {fmtPrice(search.idealPrice)} and {fmtMiles(search.idealMiles)}.</>}
          {tier === "good"  && <> Within your {fmtPrice(search.maxPrice)} / {fmtMiles(search.maxMiles)} caps.</>}
          {tier === "ok"    && <> Near your {fmtPrice(search.maxPrice)} / {fmtMiles(search.maxMiles)} limit.</>}
        </span>
      </div>

      {/* specs */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px 14px" }}>
        <SpecCell icon="drive"    label="Drivetrain" value={listing.drivetrain} />
        <SpecCell icon="user"     label="Owners"     value={listing.owners} />
        <SpecCell icon="shield"   label="Accidents"  value={listing.accidents === 0 ? "None" : `${listing.accidents} reported`} accent={listing.accidents === 0 ? "var(--green)" : "var(--amber)"} />
        <SpecCell icon="palette"  label="Exterior"   value={listing.ext} />
        <SpecCell icon="calendar" label="Days listed" value={`${listing.daysListed}d`} />
        <SpecCell icon="gauge"    label="Per year"   value={`~${milesPerYear.toLocaleString()} mi`} />
      </div>

      {/* seller + VIN */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, paddingTop: 14, borderTop: "1px solid var(--line)", fontSize: 12.5, color: "var(--fg-muted)", flexWrap: "wrap" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" }}>
          <Icon name={listing.seller.type === "Dealer" ? "shield" : "user"} size={13} />
          {listing.seller.name}
          {listing.seller.rating && <span style={{ color: "var(--amber)", marginLeft: 2 }}>★ {listing.seller.rating}</span>}
        </span>
        <span style={{ color: "var(--fg-subtle)" }}>·</span>
        <span className="tnum" style={{ color: "var(--fg-subtle)", whiteSpace: "nowrap" }}>VIN {listing.vin}</span>
        {listing.drop && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, marginLeft: "auto", color: "var(--green)", whiteSpace: "nowrap" }}>
            <Icon name="trendDown" size={13} /> Price dropped {fmtPrice(listing.drop.amount)} {listing.drop.when}
          </span>
        )}
      </div>

      {/* actions */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, paddingTop: 2 }}>
        <button className="cf-btn cf-btn-ghost" onClick={(e) => { e.stopPropagation(); onSave(); }}
          style={saved ? { color: "var(--amber)", borderColor: "var(--amber-bd)", background: "var(--amber-bg)" } : undefined}>
          <Icon name={saved ? "starFill" : "star"} size={14} /> {saved ? "Saved" : "Save"}
        </button>
        <button className="cf-btn cf-btn-ghost" onClick={(e) => { e.stopPropagation(); onHide(); }}>
          <Icon name="eyeOff" size={14} /> Not interested
        </button>
        <a href={listing.url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
          className="cf-btn cf-btn-primary" style={{ marginLeft: "auto" }}>
          View on {listing.source} <Icon name="arrowUpRight" size={14} />
        </a>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create src/components/ListingCard.tsx**

```tsx
import { TIERS, fmtPrice, fmtMiles } from "../utils";
import { Icon } from "./Icon";
import { TierBadge } from "./TierBadge";
import { DealSignal } from "./DealSignal";
import { Collapse } from "./Collapse";
import { ListingDetail } from "./ListingDetail";
import type { Listing, Search, TierKey, Deal } from "../types";

interface Props {
  listing: Listing;
  tier: TierKey;
  deal: Deal;
  search: Search;
  searchChip?: string | null;
  variant?: "default" | "tinted" | "subtle" | "badge";
  density?: "comfortable" | "compact";
  expanded: boolean;
  onToggle: () => void;
  saved: boolean;
  onSave: () => void;
  onHide: () => void;
}

export function ListingCard({ listing, tier, deal, search, searchChip, variant = "default", density = "comfortable", expanded, onToggle, saved, onSave, onHide }: Props) {
  const t = TIERS[tier];
  const comfy = density !== "compact";
  const thumbW = comfy ? 132 : 92;
  const thumbH = comfy ? 92 : 64;
  const tinted = variant === "tinted";
  const priceColor = tinted ? t.color : "var(--fg)";

  return (
    <div
      className="cf-card cf-listing"
      data-expanded={expanded}
      style={{
        position: "relative", overflow: "hidden",
        background: tinted ? `color-mix(in srgb, ${t.color} 6%, var(--surface))` : undefined,
        borderColor: expanded ? "var(--line-2)" : (tinted ? t.border : undefined),
      }}
    >
      {variant === "subtle" && (
        <span style={{ position: "absolute", left: 0, top: expanded ? 18 : "22%", bottom: expanded ? "auto" : "22%", height: expanded ? 56 : "auto", width: 2.5, borderRadius: 99, background: t.color, opacity: 0.8 }} />
      )}

      <div onClick={onToggle} style={{ display: "flex", alignItems: "center", gap: comfy ? 18 : 13, padding: comfy ? "16px 18px 16px 20px" : "11px 14px", cursor: "pointer" }}>
        {/* placeholder thumb */}
        <div style={{ width: thumbW, height: thumbH, flex: "none", borderRadius: 12, background: "#16181d", boxShadow: "inset 0 0 0 1px rgba(255,255,255,.06)", display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,.12)" }}>
          <Icon name="car" size={Math.round(thumbH * 0.32)} />
        </div>

        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: comfy ? 7 : 5 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <TierBadge tier={tier} variant={variant === "badge" ? "badge" : "dot"} />
            {searchChip && (
              <span style={{ fontSize: 11.5, fontWeight: 500, color: "var(--fg-muted)", background: "var(--chip)", borderRadius: 99, padding: "2px 9px", letterSpacing: "-0.01em", whiteSpace: "nowrap" }}>
                {searchChip}
              </span>
            )}
            {listing.isNew && <span style={{ fontSize: 11.5, fontWeight: 550, color: "var(--accent)" }}>New</span>}
            {listing.drop && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: 11.5, fontWeight: 500, color: "var(--green)" }}>
                <Icon name="trendDown" size={12} />{fmtPrice(listing.drop.amount)}
              </span>
            )}
          </div>
          <div style={{ fontSize: comfy ? 16.5 : 15, fontWeight: 600, color: "var(--fg)", lineHeight: 1.25, letterSpacing: "-0.015em", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {listing.title}
          </div>
          <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", color: "var(--fg-muted)", fontSize: 13.5 }}>
            <span className="tnum" style={{ color: "var(--fg)", fontWeight: 500, whiteSpace: "nowrap" }}>{fmtMiles(listing.miles)}</span>
            <span style={{ margin: "0 9px", color: "var(--fg-subtle)", opacity: 0.55 }}>·</span>
            <span style={{ whiteSpace: "nowrap" }}>{listing.city}</span>
            <span style={{ margin: "0 9px", color: "var(--fg-subtle)", opacity: 0.55 }}>·</span>
            <span className="tnum" style={{ whiteSpace: "nowrap" }}>{listing.distance} mi away</span>
            <span style={{ margin: "0 9px", color: "var(--fg-subtle)", opacity: 0.55 }}>·</span>
            <span style={{ color: "var(--fg-subtle)", whiteSpace: "nowrap" }}>{listing.source}</span>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: comfy ? 8 : 6, paddingLeft: 8, flex: "none" }}>
          <div className="tnum" style={{ fontSize: comfy ? 23 : 19, fontWeight: 600, color: priceColor, letterSpacing: "-0.02em", lineHeight: 1 }}>
            {fmtPrice(listing.price)}
          </div>
          <DealSignal deal={deal} />
        </div>

        <div className="cf-listing-actions" style={{ display: "flex", alignItems: "center", gap: 2, flex: "none", marginLeft: 4 }} onClick={(e) => e.stopPropagation()}>
          <button className="cf-iconbtn" onClick={onSave} title={saved ? "Saved" : "Save"} style={saved ? { color: "var(--amber)", opacity: 1 } : undefined}>
            <Icon name={saved ? "starFill" : "star"} size={15} />
          </button>
          <button className="cf-iconbtn cf-chev" onClick={onToggle} data-open={expanded} title={expanded ? "Collapse" : "Details"}>
            <Icon name="chevD" size={15} />
          </button>
        </div>
      </div>

      <Collapse open={expanded}>
        <ListingDetail listing={listing} tier={tier} deal={deal} search={search} saved={saved} onSave={onSave} onHide={onHide} />
      </Collapse>
    </div>
  );
}
```

- [ ] **Step 5: Create src/components/TopPick.tsx**

```tsx
import { TIERS, fmtPrice, fmtMiles } from "../utils";
import { Icon } from "./Icon";
import { DealSignal } from "./DealSignal";
import { Collapse } from "./Collapse";
import { ListingDetail } from "./ListingDetail";
import type { Listing, Search, TierKey, Deal } from "../types";

interface Props {
  listing: Listing;
  tier: TierKey;
  deal: Deal;
  search: Search;
  expanded: boolean;
  onToggle: () => void;
  saved: boolean;
  onSave: () => void;
  onHide: () => void;
}

export function TopPick({ listing, tier, deal, search, expanded, onToggle, saved, onSave, onHide }: Props) {
  const t = TIERS[tier];
  return (
    <div className="cf-card" style={{ padding: 0, overflow: "hidden", borderColor: "var(--line-2)", background: `linear-gradient(180deg, color-mix(in srgb, ${t.color} 7%, var(--surface)), var(--surface))` }}>
      <div onClick={onToggle} style={{ display: "flex", alignItems: "center", gap: 16, padding: 16, cursor: "pointer" }}>
        <div style={{ width: 108, height: 76, flex: "none", borderRadius: 10, background: "#16181d", boxShadow: "inset 0 0 0 1px rgba(255,255,255,.06)", display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,.12)" }}>
          <Icon name="car" size={24} />
        </div>
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11.5, fontWeight: 600, color: t.color, letterSpacing: "0.02em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
            <Icon name="bolt" size={13} /> Top pick for you
          </div>
          <div style={{ fontSize: 17, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.015em", lineHeight: 1.2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {listing.title}
          </div>
          <div style={{ fontSize: 13.5, color: "var(--fg-muted)" }}>
            {fmtMiles(listing.miles)} · {listing.city} · {listing.distance} mi
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 7, flex: "none" }}>
          <div className="tnum" style={{ fontSize: 24, fontWeight: 600, color: t.color, letterSpacing: "-0.025em", lineHeight: 1 }}>
            {fmtPrice(listing.price)}
          </div>
          <DealSignal deal={deal} />
        </div>
        <button className="cf-iconbtn cf-chev" data-open={expanded} style={{ flex: "none" }}>
          <Icon name="chevD" size={15} />
        </button>
      </div>
      <Collapse open={expanded}>
        <ListingDetail listing={listing} tier={tier} deal={deal} search={search} saved={saved} onSave={onSave} onHide={onHide} />
      </Collapse>
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/components/
git commit -m "feat: add DealGauge, SpecCell, ListingDetail, ListingCard, TopPick"
```

---

## Task 6: TopBar, ProfileBar, AllSummary, ScanFooter

**Files:**
- Create: `src/components/TopBar.tsx`
- Create: `src/components/ProfileBar.tsx`
- Create: `src/components/AllSummary.tsx`
- Create: `src/components/ScanFooter.tsx`

- [ ] **Step 1: Create src/components/TopBar.tsx**

```tsx
import { Icon } from "./Icon";
import type { Search } from "../types";

type View = "dashboard" | "setup" | "email" | "compare";

interface Props {
  view: View;
  onNav: (v: View) => void;
  newCount: number;
  searches: Search[];
  activeId: string;
  onSelectSearch: (id: string) => void;
  onNewSearch: () => void;
}

export function TopBar({ view, onNav, newCount, searches, activeId, onSelectSearch, onNewSearch }: Props) {
  return (
    <header style={{ height: 60, flex: "none", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 26px", borderBottom: "1px solid var(--line)", background: "color-mix(in srgb, var(--bg) 78%, transparent)", backdropFilter: "saturate(160%) blur(16px)", position: "sticky", top: 0, zIndex: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 25, height: 25, borderRadius: 8, background: "rgba(255,255,255,.06)", boxShadow: "inset 0 0 0 1px var(--line-2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Icon name="car" size={15} />
          </div>
          <span style={{ fontSize: 15.5, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.02em" }}>CarFinder</span>
        </div>

        {/* Nav tabs */}
        <nav style={{ display: "flex", alignItems: "center", gap: 2 }}>
          {(["dashboard", "email"] as const).map((id) => (
            <button key={id} onClick={() => onNav(id)} className="cf-tab" data-active={view === id}>
              {id === "dashboard" ? "Dashboard" : "Email alert"}
              {id === "email" && newCount > 0 && <span className="cf-tab-badge">{newCount}</span>}
            </button>
          ))}
        </nav>
      </div>

      {/* Search selector */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
          <button className="cf-tab" data-active={activeId === "all"} onClick={() => onSelectSearch("all")}>All</button>
          {searches.map((s) => (
            <button key={s.id} className="cf-tab" data-active={activeId === s.id} onClick={() => onSelectSearch(s.id)}>
              {s.make} {s.model}
            </button>
          ))}
        </div>
        <button className="cf-btn cf-btn-ghost" style={{ height: 30, padding: "0 10px", fontSize: 13 }} onClick={onNewSearch}>
          <Icon name="plus" size={13} /> New
        </button>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Create src/components/ProfileBar.tsx**

```tsx
import { fmtPrice, fmtMiles } from "../utils";
import { Icon } from "./Icon";
import type { Search } from "../types";

export function ProfileBar({ search, onEdit }: { search: Search; onEdit: () => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "var(--fg)", margin: 0, letterSpacing: "-0.03em" }}>
          {search.year} {search.make} {search.model} {search.trim}
        </h1>
        <p style={{ fontSize: 13, color: "var(--fg-muted)", margin: "4px 0 0", letterSpacing: "-0.01em" }}>
          Up to {fmtPrice(search.maxPrice)} · {fmtMiles(search.maxMiles)} max · {search.radius} mi of {search.zip} · every {search.intervalHours}h
        </p>
      </div>
      <button className="cf-btn cf-btn-ghost" onClick={onEdit}>
        <Icon name="palette" size={14} /> Edit search
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Create src/components/AllSummary.tsx**

```tsx
import { fmtPrice } from "../utils";
import type { Search } from "../types";

export function AllSummary({ searches, counts }: { searches: Search[]; counts: Record<string, number> }) {
  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 600, color: "var(--fg)", margin: "0 0 14px", letterSpacing: "-0.03em" }}>
        All searches
      </h1>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {searches.map((s) => (
          <div key={s.id} className="cf-card" style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.015em" }}>
              {s.year} {s.make} {s.model}
            </span>
            <span style={{ fontSize: 12.5, color: "var(--fg-muted)" }}>
              {counts[s.id] ?? 0} matches · up to {fmtPrice(s.maxPrice)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create src/components/ScanFooter.tsx**

```tsx
import { Icon } from "./Icon";

interface Props {
  scanning: boolean;
  lastScan: string;
  intervalHours: number;
  isAll: boolean;
  searchCount: number;
  onScan: () => void;
}

export function ScanFooter({ scanning, lastScan, intervalHours, isAll, searchCount, onScan }: Props) {
  return (
    <div style={{ position: "sticky", bottom: 0, zIndex: 15, borderTop: "1px solid var(--line)", background: "color-mix(in srgb, var(--bg) 72%, transparent)", backdropFilter: "saturate(160%) blur(16px)" }}>
      <div style={{ maxWidth: 940, margin: "0 auto", padding: "13px 30px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11, fontSize: 13.5, color: "var(--fg-muted)", letterSpacing: "-0.01em" }}>
          <span style={{ display: "flex", color: scanning ? "var(--accent)" : "var(--fg-subtle)" }} className={scanning ? "cf-spin" : ""}>
            <Icon name={scanning ? "refresh" : "clock"} size={15} />
          </span>
          {scanning
            ? <span className="cf-breath" style={{ color: "var(--fg)" }}>Scanning {isAll ? `${searchCount} searches` : "listing sites"}…</span>
            : <span>Last scan <span style={{ color: "var(--fg)", fontWeight: 500 }}>{lastScan}</span> · next in {intervalHours}h</span>}
        </div>
        <button className="cf-btn cf-btn-primary" onClick={onScan} disabled={scanning}>
          <span className={scanning ? "cf-spin" : ""} style={{ display: "flex" }}><Icon name="refresh" size={15} /></span>
          {scanning ? "Scanning…" : "Scan now"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/components/
git commit -m "feat: add TopBar, ProfileBar, AllSummary, ScanFooter"
```

---

## Task 7: App state hook and main entry

**Files:**
- Create: `src/useAppState.ts`
- Create: `src/main.tsx`

- [ ] **Step 1: Create src/useAppState.ts**

```ts
import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import { tierFor, dealFor } from "./utils";
import type { Search, Listing, EnrichedListing } from "./types";

export interface AppState {
  searches: Search[];
  listingsBySearch: Record<string, Listing[]>;
  saved: Set<string>;
  hidden: Set<string>;
  expanded: Set<string>;
  scanning: boolean;
  lastScan: string;
  loading: boolean;
  error: string | null;
  enrichedFor: (searchId: string) => EnrichedListing[];
  toggleSave: (searchId: string, listingId: string) => void;
  toggleHide: (searchId: string, listingId: string) => void;
  toggleExpand: (listingId: string) => void;
  resetHidden: (searchId: string) => void;
  scan: (searchId?: string) => void;
  createSearch: (s: Partial<Search>) => Promise<void>;
  updateSearch: (id: string, s: Partial<Search>) => Promise<void>;
  deleteSearch: (id: string) => Promise<void>;
  reload: () => void;
}

export function useAppState(): AppState {
  const [searches, setSearches] = useState<Search[]>([]);
  const [listingsBySearch, setListingsBySearch] = useState<Record<string, Listing[]>>({});
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [scanning, setScanning] = useState(false);
  const [lastScan, setLastScan] = useState("never");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.getSearches().then(async ({ searches: ss }) => {
      if (cancelled) return;
      setSearches(ss);
      const bySearch: Record<string, Listing[]> = {};
      await Promise.all(ss.map(async (s) => {
        try {
          const { listings } = await api.getListings(s.id);
          bySearch[s.id] = listings;
        } catch {
          bySearch[s.id] = [];
        }
      }));
      if (!cancelled) {
        setListingsBySearch(bySearch);
        setLoading(false);
      }
    }).catch((e: Error) => {
      if (!cancelled) { setError(e.message); setLoading(false); }
    });
    return () => { cancelled = true; };
  }, [tick]);

  const enrichedFor = useCallback((searchId: string): EnrichedListing[] => {
    const search = searches.find((s) => s.id === searchId);
    if (!search) return [];
    const listings = listingsBySearch[searchId] ?? [];
    return listings
      .filter((l) => !hidden.has(l.id))
      .map((l) => ({ ...l, tier: tierFor(l, search), deal: dealFor(l), searchId }));
  }, [searches, listingsBySearch, hidden]);

  const toggleSave = useCallback((searchId: string, listingId: string) => {
    setSaved((prev) => {
      const next = new Set(prev);
      if (next.has(listingId)) {
        next.delete(listingId);
        api.unsaveListing(searchId, listingId).catch(() => {});
      } else {
        next.add(listingId);
        api.savelisting(searchId, listingId).catch(() => {});
      }
      return next;
    });
  }, []);

  const toggleHide = useCallback((searchId: string, listingId: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      next.add(listingId);
      api.hideListing(searchId, listingId).catch(() => {});
      return next;
    });
  }, []);

  const toggleExpand = useCallback((listingId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(listingId)) next.delete(listingId);
      else next.add(listingId);
      return next;
    });
  }, []);

  const resetHidden = useCallback((searchId: string) => {
    setHidden(new Set());
    api.unhideAll(searchId).catch(() => {});
  }, []);

  const scan = useCallback((searchId?: string) => {
    setScanning(true);
    const p = searchId ? api.scanSearch(searchId) : api.scanAll();
    p.finally(() => {
      setScanning(false);
      setLastScan(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
      reload();
    });
  }, [reload]);

  const createSearch = useCallback(async (s: Partial<Search>) => {
    await api.createSearch(s);
    reload();
  }, [reload]);

  const updateSearch = useCallback(async (id: string, s: Partial<Search>) => {
    await api.updateSearch(id, s);
    reload();
  }, [reload]);

  const deleteSearch = useCallback(async (id: string) => {
    await api.deleteSearch(id);
    reload();
  }, [reload]);

  return { searches, listingsBySearch, saved, hidden, expanded, scanning, lastScan, loading, error, enrichedFor, toggleSave, toggleHide, toggleExpand, resetHidden, scan, createSearch, updateSearch, deleteSearch, reload };
}
```

- [ ] **Step 2: Create src/main.tsx**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./tokens.css";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 3: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/useAppState.ts src/main.tsx
git commit -m "feat: add useAppState hook and main entry"
```

---

## Task 8: Dashboard, SetupScreen, EmailScreen screens

**Files:**
- Create: `src/screens/Dashboard.tsx`
- Create: `src/screens/SetupScreen.tsx`
- Create: `src/screens/EmailScreen.tsx`
- Create: `src/screens/CompareModal.tsx`

- [ ] **Step 1: Create src/screens/Dashboard.tsx**

```tsx
import { useMemo, useState, useEffect } from "react";
import { TIERS, fmtPrice, fmtMiles } from "../utils";
import { StatCard } from "../components/StatCard";
import { ListingCard } from "../components/ListingCard";
import { TopPick } from "../components/TopPick";
import { ProfileBar } from "../components/ProfileBar";
import { AllSummary } from "../components/AllSummary";
import { ScanFooter } from "../components/ScanFooter";
import { Icon } from "../components/Icon";
import type { AppState } from "../useAppState";
import type { Search, TierKey, EnrichedListing } from "../types";

type FilterKey = TierKey | "all" | "saved";

interface Props extends AppState {
  activeId: string;
  onEdit: (search: Search) => void;
  onCompare: () => void;
}

const ORDER: Record<TierKey, number> = { ideal: 0, good: 1, ok: 2 };

export function Dashboard({ searches, activeId, enrichedFor, saved, hidden, expanded, scanning, lastScan, toggleSave, toggleHide, toggleExpand, resetHidden, scan, onEdit, onCompare }: Props) {
  const isAll = activeId === "all";
  const activeSearch = isAll ? null : searches.find((s) => s.id === activeId) ?? null;

  const enriched = useMemo<EnrichedListing[]>(() => {
    const rows = isAll
      ? searches.flatMap((s) => enrichedFor(s.id).map((l) => ({ ...l, _search: s })))
      : enrichedFor(activeId);
    return [...rows].sort((a, b) => ORDER[a.tier] - ORDER[b.tier] || a.deal.delta - b.deal.delta || a.price - b.price);
  }, [isAll, activeId, searches, enrichedFor, hidden]);

  const [filter, setFilter] = useState<FilterKey>("all");
  useEffect(() => { setFilter("all"); }, [activeId]);

  const tierCounts = useMemo(() => {
    const c = { all: enriched.length, ideal: 0, good: 0, ok: 0, saved: 0 };
    enriched.forEach((l) => {
      c[l.tier]++;
      if (saved.has(l.id)) c.saved++;
    });
    return c;
  }, [enriched, saved]);

  const newCount = enriched.filter((l) => l.isNew).length;
  const allListings = isAll ? searches.flatMap((s) => ([] as EnrichedListing[]).concat(enrichedFor(s.id))) : enrichedFor(activeId);
  const hiddenCount = allListings.filter((l) => hidden.has(l.id)).length;

  const pick = useMemo(() => {
    if (filter !== "all" || !enriched.length) return null;
    const ideals = enriched.filter((l) => l.tier === "ideal");
    return (ideals.length ? ideals : enriched)[0];
  }, [enriched, filter]);

  const shown = useMemo(() => {
    let rows = filter === "saved" ? enriched.filter((l) => saved.has(l.id))
              : filter === "all" ? enriched
              : enriched.filter((l) => l.tier === filter);
    if (pick) rows = rows.filter((l) => l.id !== pick.id);
    return rows;
  }, [enriched, filter, saved, pick]);

  const savedCount = [...saved].length;
  const intervalHours = isAll
    ? Math.min(...(searches.map((s) => s.intervalHours).length ? searches.map((s) => s.intervalHours) : [2]))
    : (activeSearch?.intervalHours ?? 2);
  const bestPrice = enriched.length ? fmtPrice(Math.min(...enriched.map((l) => l.price))) : "—";
  const FILTERS: [FilterKey, string][] = [["all", "All"], ["ideal", "Ideal"], ["good", "Good"], ["ok", "Ok"], ["saved", "Saved"]];

  const getSearch = (l: EnrichedListing) => searches.find((s) => s.id === l.searchId)!;

  return (
    <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", minHeight: "calc(100vh - 60px)" }}>
      <div style={{ flex: 1, maxWidth: 940, width: "100%", margin: "0 auto", padding: "30px 30px 128px", display: "flex", flexDirection: "column", gap: 22 }}>
        {isAll
          ? <AllSummary searches={searches} counts={Object.fromEntries(searches.map((s) => [s.id, enrichedFor(s.id).length]))} />
          : activeSearch && <ProfileBar search={activeSearch} onEdit={() => onEdit(activeSearch)} />}

        {/* Stats */}
        <div style={{ display: "flex", gap: 14 }}>
          <StatCard label="Total matches" value={enriched.length} sub={isAll ? `across ${searches.length} searches` : "across listing sites"} icon="car" />
          <StatCard label="New since last scan" value={newCount} sub={newCount ? "ready to email" : "all caught up"} icon="sparkle" />
          <StatCard label="Best price" value={bestPrice} sub={isAll ? "lowest across hunts" : `under your ${activeSearch ? fmtPrice(activeSearch.maxPrice) : ""} cap`} icon="tag" />
        </div>

        {/* Top pick */}
        {pick && (
          <div className="cf-rise">
            <TopPick listing={pick} tier={pick.tier} deal={pick.deal} search={getSearch(pick)}
              expanded={expanded.has(pick.id)} onToggle={() => toggleExpand(pick.id)}
              saved={saved.has(pick.id)} onSave={() => toggleSave(pick.searchId, pick.id)} onHide={() => toggleHide(pick.searchId, pick.id)} />
          </div>
        )}

        {/* List header + filters */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 4, gap: 16, flexWrap: "wrap" }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--fg)", margin: 0, display: "flex", alignItems: "baseline", gap: 10, letterSpacing: "-0.02em", whiteSpace: "nowrap" }}>
            {filter === "saved" ? "Saved" : "Matching listings"}
            <span className="tnum" style={{ fontSize: 13.5, fontWeight: 500, color: "var(--fg-subtle)" }}>
              {shown.length + (pick && filter === "all" ? 1 : 0)}
            </span>
            {hiddenCount > 0 && (
              <button className="cf-linkbtn" onClick={() => resetHidden(activeId)}>{hiddenCount} hidden · reset</button>
            )}
          </h2>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {savedCount >= 2 && (
              <button className="cf-btn cf-btn-ghost" onClick={onCompare} style={{ height: 32 }}>
                <Icon name="columns" size={14} /> Compare <span className="tnum" style={{ color: "var(--fg-muted)" }}>{savedCount}</span>
              </button>
            )}
            <div style={{ display: "flex", gap: 2 }}>
              {FILTERS.map(([id, label]) => (
                <button key={id} onClick={() => setFilter(id)} className="cf-filter" data-active={filter === id}
                  style={["ideal", "good", "ok"].includes(id) ? { "--fdot": `var(--${id === "ideal" ? "green" : id === "good" ? "blue" : "amber"})` } as React.CSSProperties : undefined}>
                  {["ideal", "good", "ok"].includes(id) && <span className="cf-fdot" />}
                  {id === "saved" && <Icon name="star" size={12} />}
                  {label} <span className="tnum" style={{ opacity: 0.5 }}>{tierCounts[id as keyof typeof tierCounts]}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {filter === "saved" && savedCount >= 2 && (
          <button onClick={onCompare} className="cf-compare-nudge">
            <span style={{ display: "inline-flex", alignItems: "center", gap: 9 }}>
              <Icon name="columns" size={15} /> Line these {savedCount} up side by side
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "var(--accent)", fontWeight: 550 }}>
              Compare <Icon name="arrowUpRight" size={13} />
            </span>
          </button>
        )}

        {/* Listings */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: -6 }}>
          {shown.map((l, i) => (
            <div key={l.id} className="cf-rise" style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}>
              <ListingCard listing={l} tier={l.tier} deal={l.deal} search={getSearch(l)}
                searchChip={isAll ? `${getSearch(l).make} ${getSearch(l).model}` : null}
                expanded={expanded.has(l.id)} onToggle={() => toggleExpand(l.id)}
                saved={saved.has(l.id)} onSave={() => toggleSave(l.searchId, l.id)} onHide={() => toggleHide(l.searchId, l.id)} />
            </div>
          ))}
          {shown.length === 0 && (
            <div style={{ padding: "48px 20px", textAlign: "center", color: "var(--fg-subtle)", fontSize: 14 }}>
              {filter === "saved" ? "No saved listings yet — tap the ★ on any match to save it." : "Nothing in this tier right now."}
            </div>
          )}
        </div>
      </div>

      <ScanFooter scanning={scanning} lastScan={lastScan} intervalHours={intervalHours}
        isAll={isAll} searchCount={searches.length} onScan={() => scan(isAll ? undefined : activeId)} />
    </div>
  );
}
```

- [ ] **Step 2: Create src/screens/SetupScreen.tsx**

```tsx
import { useState } from "react";
import { Icon } from "../components/Icon";
import type { Search } from "../types";

interface Props {
  search?: Partial<Search>;
  mode?: "new" | "edit";
  onSave: (s: Partial<Search>) => Promise<void>;
  onCancel: () => void;
}

const DEFAULT: Partial<Search> = {
  year: new Date().getFullYear() - 4,
  make: "", model: "", trim: "",
  maxPrice: 25000, idealPrice: 20000,
  maxMiles: 100000, idealMiles: 60000,
  zip: "", radius: 100, intervalHours: 2,
  email: "",
};

export function SetupScreen({ search, mode = "new", onSave, onCancel }: Props) {
  const [f, setF] = useState<Partial<Search>>({ ...DEFAULT, ...search });
  const [saving, setSaving] = useState(false);
  const up = (k: keyof Search) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF((s) => ({ ...s, [k]: e.target.value }));
  const upN = (k: keyof Search) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF((s) => ({ ...s, [k]: e.target.value === "" ? "" : Number(e.target.value) }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try { await onSave({ ...f, city: f.zip ?? "" }); }
    finally { setSaving(false); }
  };

  const Field = ({ label, hint, children, span }: { label: string; hint?: string; children: React.ReactNode; span?: number }) => (
    <label style={{ display: "flex", flexDirection: "column", gap: 8, gridColumn: span ? `span ${span}` : "auto" }}>
      <span style={{ fontSize: 13, fontWeight: 550, color: "var(--fg)", letterSpacing: "-0.01em" }}>
        {label}{hint && <span style={{ color: "var(--fg-subtle)", fontWeight: 450, marginLeft: 7 }}>{hint}</span>}
      </span>
      {children}
    </label>
  );

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
            <Field label="Make" span={2}><input className="cf-input" value={f.make ?? ""} onChange={up("make")} placeholder="Toyota" required /></Field>
            <Field label="Model" span={2}><input className="cf-input" value={f.model ?? ""} onChange={up("model")} placeholder="Sienna" required /></Field>
            <Field label="Trim" hint="optional" span={2}><input className="cf-input" value={f.trim ?? ""} onChange={up("trim")} placeholder="Limited Platinum" /></Field>
            <Field label="Year" span={2}><input className="cf-input" type="number" value={f.year ?? ""} onChange={upN("year")} min={1990} max={new Date().getFullYear()} required /></Field>
          </div>
        </section>

        {/* Price & mileage */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="tag" size={15} /> Price &amp; mileage</div>
          <div className="cf-grid">
            <Field label="Max price" hint="hard cap" span={3}>
              <div className="cf-input-wrap"><span className="cf-prefix">$</span><input className="cf-input cf-has-prefix" type="number" value={f.maxPrice ?? ""} onChange={upN("maxPrice")} required /></div>
            </Field>
            <Field label="Ideal price" hint="for Ideal tier" span={3}>
              <div className="cf-input-wrap"><span className="cf-prefix">$</span><input className="cf-input cf-has-prefix" type="number" value={f.idealPrice ?? ""} onChange={upN("idealPrice")} required /></div>
            </Field>
            <Field label="Max mileage" hint="hard cap" span={3}>
              <div className="cf-input-wrap"><input className="cf-input cf-has-suffix" type="number" value={f.maxMiles ?? ""} onChange={upN("maxMiles")} required /><span className="cf-suffix">mi</span></div>
            </Field>
            <Field label="Ideal mileage" hint="for Ideal tier" span={3}>
              <div className="cf-input-wrap"><input className="cf-input cf-has-suffix" type="number" value={f.idealMiles ?? ""} onChange={upN("idealMiles")} required /><span className="cf-suffix">mi</span></div>
            </Field>
          </div>
          <div className="cf-tierlegend">
            <span><span className="cf-lg" style={{ background: "var(--green)" }} /> Ideal = under ideal price &amp; miles</span>
            <span><span className="cf-lg" style={{ background: "var(--blue)" }} /> Good = under both hard caps</span>
            <span><span className="cf-lg" style={{ background: "var(--amber)" }} /> Ok = within caps, near a limit</span>
          </div>
        </section>

        {/* Location */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="pin" size={15} /> Location</div>
          <div className="cf-grid">
            <Field label="ZIP code" span={2}><input className="cf-input" value={f.zip ?? ""} onChange={up("zip")} placeholder="72761" required /></Field>
            <Field label="Search radius" span={4}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <input type="range" min={10} max={300} step={5} value={f.radius ?? 100} onChange={upN("radius")} className="cf-range" style={{ flex: 1 }} />
                <span className="tnum" style={{ fontSize: 14.5, fontWeight: 550, color: "var(--fg)", minWidth: 64, textAlign: "right", letterSpacing: "-0.01em" }}>{f.radius} mi</span>
              </div>
            </Field>
          </div>
        </section>

        {/* Alerts */}
        <section className="cf-card cf-form-sec">
          <div className="cf-form-head"><Icon name="mail" size={15} /> Email alerts</div>
          <div className="cf-grid">
            <Field label="Your email" span={4}><input className="cf-input" type="email" value={f.email ?? ""} onChange={up("email")} placeholder="you@example.com" required /></Field>
            <Field label="Scan interval" span={2}>
              <div className="cf-input-wrap"><input className="cf-input cf-has-suffix" type="number" value={f.intervalHours ?? 2} onChange={upN("intervalHours")} min={1} max={24} /><span className="cf-suffix">hrs</span></div>
            </Field>
          </div>
        </section>

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button type="button" className="cf-btn cf-btn-ghost" onClick={onCancel}>Cancel</button>
          <button type="submit" className="cf-btn cf-btn-primary" disabled={saving}>
            {saving ? "Saving…" : mode === "new" ? "Start hunting" : "Save changes"}
          </button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Create src/screens/EmailScreen.tsx**

```tsx
import { useMemo } from "react";
import { fmtPrice, fmtMiles, TIERS, dealFor, tierFor } from "../utils";
import { Icon } from "../components/Icon";
import { TierBadge } from "../components/TierBadge";
import type { AppState } from "../useAppState";

export function EmailScreen({ searches, listingsBySearch }: Pick<AppState, "searches" | "listingsBySearch">) {
  const newListings = useMemo(() => {
    return searches.flatMap((s) => {
      const listings = listingsBySearch[s.id] ?? [];
      return listings
        .filter((l) => l.isNew)
        .map((l) => ({ ...l, tier: tierFor(l, s), deal: dealFor(l), search: s }));
    });
  }, [searches, listingsBySearch]);

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "30px 26px 60px" }}>
      <div style={{ marginBottom: 26 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "var(--fg)", margin: "0 0 8px", letterSpacing: "-0.03em" }}>Email alert preview</h1>
        <p style={{ fontSize: 14, color: "var(--fg-muted)", margin: 0, letterSpacing: "-0.01em" }}>
          This is what your next email will contain — {newListings.length} new {newListings.length === 1 ? "match" : "matches"} since the last scan.
        </p>
      </div>

      {/* Email chrome */}
      <div className="cf-card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)", display: "flex", flexDirection: "column", gap: 4 }}>
          <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>From: <span style={{ color: "var(--fg)" }}>CarFinder &lt;alerts@carfinder.app&gt;</span></div>
          <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>Subject: <span style={{ color: "var(--fg)", fontWeight: 550 }}>🚗 {newListings.length} new {newListings.length === 1 ? "match" : "matches"} for your searches</span></div>
        </div>
        <div style={{ padding: "24px 20px", display: "flex", flexDirection: "column", gap: 16 }}>
          {newListings.length === 0 && (
            <div style={{ textAlign: "center", padding: "32px 0", color: "var(--fg-subtle)", fontSize: 14 }}>
              No new matches since last scan. Check back after the next scan runs.
            </div>
          )}
          {newListings.map((l) => {
            const t = TIERS[l.tier];
            return (
              <div key={l.id} style={{ padding: "14px 16px", borderRadius: 10, background: "var(--surface-2)", border: "1px solid var(--line)" }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 5, flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <TierBadge tier={l.tier} variant="badge" />
                      <span style={{ fontSize: 11.5, fontWeight: 500, color: "var(--fg-muted)", background: "var(--chip)", borderRadius: 99, padding: "2px 9px" }}>
                        {l.search.make} {l.search.model}
                      </span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.015em" }}>{l.title}</div>
                    <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>
                      {fmtMiles(l.miles)} · {l.city} · {l.distance} mi away · {l.source}
                    </div>
                    {l.deal.delta < 0 && (
                      <div style={{ fontSize: 12.5, color: "var(--green)", display: "flex", alignItems: "center", gap: 4 }}>
                        <Icon name="trendDown" size={12} /> {l.deal.label} — {fmtPrice(Math.abs(l.deal.delta))} under market
                      </div>
                    )}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flex: "none" }}>
                    <div className="tnum" style={{ fontSize: 20, fontWeight: 600, color: t.color, letterSpacing: "-0.02em" }}>{fmtPrice(l.price)}</div>
                    <a href={l.url} target="_blank" rel="noreferrer" className="cf-btn cf-btn-primary" style={{ height: 30, fontSize: 12.5 }}>
                      View <Icon name="arrowUpRight" size={13} />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create src/screens/CompareModal.tsx**

```tsx
import { useMemo } from "react";
import { fmtPrice, fmtMiles, TIERS, tierFor, dealFor } from "../utils";
import { Icon } from "../components/Icon";
import { TierBadge } from "../components/TierBadge";
import { DealGauge } from "../components/DealGauge";
import type { AppState } from "../useAppState";

interface Props extends Pick<AppState, "searches" | "listingsBySearch" | "saved"> {
  onClose: () => void;
}

const ROWS = [
  { key: "price",       label: "Price",       fmt: (v: unknown) => fmtPrice(v as number) },
  { key: "miles",       label: "Mileage",     fmt: (v: unknown) => fmtMiles(v as number) },
  { key: "drivetrain",  label: "Drivetrain",  fmt: (v: unknown) => String(v) },
  { key: "owners",      label: "Owners",      fmt: (v: unknown) => String(v) },
  { key: "accidents",   label: "Accidents",   fmt: (v: unknown) => (v as number) === 0 ? "None" : String(v) },
  { key: "daysListed",  label: "Days listed", fmt: (v: unknown) => `${v}d` },
  { key: "source",      label: "Source",      fmt: (v: unknown) => String(v) },
  { key: "city",        label: "Location",    fmt: (v: unknown) => String(v) },
];

export function CompareModal({ searches, listingsBySearch, saved, onClose }: Props) {
  const listings = useMemo(() => {
    return searches.flatMap((s) => {
      const ls = listingsBySearch[s.id] ?? [];
      return ls.filter((l) => saved.has(l.id)).map((l) => ({
        ...l,
        tier: tierFor(l, s),
        deal: dealFor(l),
        search: s,
      }));
    });
  }, [searches, listingsBySearch, saved]);

  return (
    <div className="cf-overlay" onClick={onClose}>
      <div className="cf-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--fg)", margin: 0, letterSpacing: "-0.025em" }}>
            Compare saved listings
          </h2>
          <button className="cf-iconbtn" onClick={onClose}><Icon name="plus" size={15} style={{ transform: "rotate(45deg)" } as React.CSSProperties} /></button>
        </div>

        {listings.length < 2 && (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--fg-subtle)", fontSize: 14 }}>
            Save at least 2 listings (tap ★) to compare them here.
          </div>
        )}

        {listings.length >= 2 && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ width: 120, padding: "8px 12px", textAlign: "left", fontSize: 12.5, color: "var(--fg-subtle)", fontWeight: 500 }} />
                  {listings.map((l) => (
                    <th key={l.id} style={{ padding: "8px 12px", textAlign: "left", minWidth: 200 }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                        <TierBadge tier={l.tier} variant="badge" />
                        <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.015em" }}>{l.title}</div>
                        <a href={l.url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: "var(--accent)", display: "inline-flex", alignItems: "center", gap: 3 }}>
                          View <Icon name="arrowUpRight" size={11} />
                        </a>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map(({ key, label, fmt }) => (
                  <tr key={key} style={{ borderTop: "1px solid var(--line)" }}>
                    <td style={{ padding: "10px 12px", fontSize: 12.5, color: "var(--fg-subtle)", fontWeight: 500 }}>{label}</td>
                    {listings.map((l) => (
                      <td key={l.id} className="tnum" style={{ padding: "10px 12px", fontSize: 13.5, fontWeight: 500, color: "var(--fg)" }}>
                        {fmt((l as Record<string, unknown>)[key])}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr style={{ borderTop: "1px solid var(--line)" }}>
                  <td style={{ padding: "10px 12px", fontSize: 12.5, color: "var(--fg-subtle)", fontWeight: 500 }}>Deal</td>
                  {listings.map((l) => (
                    <td key={l.id} style={{ padding: "10px 12px" }}>
                      <DealGauge listing={l} deal={l.deal} />
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/screens/
git commit -m "feat: add Dashboard, SetupScreen, EmailScreen, CompareModal screens"
```

---

## Task 9: App.tsx root + dev server smoke test

**Files:**
- Create: `src/App.tsx`

- [ ] **Step 1: Create src/App.tsx**

```tsx
import { useState } from "react";
import { useAppState } from "./useAppState";
import { TopBar } from "./components/TopBar";
import { Dashboard } from "./screens/Dashboard";
import { SetupScreen } from "./screens/SetupScreen";
import { EmailScreen } from "./screens/EmailScreen";
import { CompareModal } from "./screens/CompareModal";
import type { Search } from "./types";

type View = "dashboard" | "setup" | "email";

export function App() {
  const state = useAppState();
  const [view, setView] = useState<View>("dashboard");
  const [activeId, setActiveId] = useState("all");
  const [editingSearch, setEditingSearch] = useState<Partial<Search> | null>(null);
  const [setupMode, setSetupMode] = useState<"new" | "edit">("new");
  const [showCompare, setShowCompare] = useState(false);

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

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--fg-muted)", fontSize: 14 }}>
        <span className="cf-spin" style={{ marginRight: 10 }}>⟳</span> Loading…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", gap: 12, color: "var(--fg-muted)", fontSize: 14 }}>
        <div style={{ color: "var(--amber)" }}>Could not connect to backend</div>
        <div style={{ fontSize: 12.5, color: "var(--fg-subtle)" }}>{error}</div>
        <button className="cf-btn cf-btn-ghost" onClick={state.reload}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <TopBar view={view} onNav={(v) => setView(v as View)} newCount={newCount}
        searches={searches} activeId={activeId}
        onSelectSearch={setActiveId} onNewSearch={handleNewSearch} />

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
```

- [ ] **Step 2: Create .env.local pointing at local backend**

```bash
cd /Users/marcos/carfinder-ui
echo "VITE_API_URL=http://localhost:5000
VITE_USER_ID=user_marcos" > .env.local
```

- [ ] **Step 3: Start dev server and verify it compiles**

```bash
cd /Users/marcos/carfinder-ui && npm run dev
```

Expected: Vite starts on `http://localhost:5173`. No TypeScript errors in terminal. Browser shows CarFinder header. If backend isn't running, you'll see the "Could not connect" error screen — that's expected.

- [ ] **Step 4: Fix any TypeScript errors**

Run `npm run build` (which runs `tsc`) and fix any type errors before committing:

```bash
cd /Users/marcos/carfinder-ui && npm run build
```

Expected: `dist/` created, no type errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/marcos/carfinder-ui
git add src/App.tsx .env.local
git commit -m "feat: wire up App.tsx root with all screens and state"
```

---

## Task 10: Deploy to Vercel

**Files:**
- No new files — uses existing `vercel.json`

- [ ] **Step 1: Install Vercel CLI**

```bash
npm install -g vercel
```

- [ ] **Step 2: Build the project**

```bash
cd /Users/marcos/carfinder-ui && npm run build
```

Expected: `dist/` folder created with `index.html` + assets.

- [ ] **Step 3: Deploy**

```bash
cd /Users/marcos/carfinder-ui && vercel --prod
```

When prompted:
- Set up project: **Yes**
- Which scope: your Vercel account
- Link to existing: **No**
- Project name: `carfinder-ui`
- Directory: `.` (current)
- Override settings: **No**

- [ ] **Step 4: Set environment variables in Vercel**

```bash
vercel env add VITE_API_URL production
# enter: https://melodious-consideration-production-845d.up.railway.app

vercel env add VITE_USER_ID production
# enter: user_marcos
```

- [ ] **Step 5: Re-deploy with env vars**

```bash
cd /Users/marcos/carfinder-ui && vercel --prod
```

Expected: Deployment URL printed. Open it — app loads, connects to Railway backend.

- [ ] **Step 6: Final commit with Vercel URL in notes**

```bash
cd /Users/marcos/carfinder-ui
git tag v0.1.0
git push origin main --tags
```

---

## Self-Review

**Spec coverage:**
- ✅ Dashboard with TopPick, ListingCard, filters (all/ideal/good/ok/saved) — Task 8
- ✅ Setup screen with all fields from design (vehicle, price/miles, location, alerts) — Task 8
- ✅ Email alert preview screen — Task 8
- ✅ Compare modal for saved listings — Task 8
- ✅ Design tokens exactly matching handoff (`--bg #0a0b0d`, `--surface #101216`, `--accent #4f8ff5`, `--green #6ec594`, Onest font) — Task 2
- ✅ tierFor/dealFor logic ported from data.js — Task 3
- ✅ DealGauge with gradient bar and market estimate — Task 5
- ✅ Collapse animation — Task 4
- ✅ Sticky scan footer with spin animation — Task 6
- ✅ Save/hide per listing wired to API — Task 7
- ✅ Scan now button with loading state — Task 7
- ✅ Vercel deployment — Task 10

**No placeholders found.**

**Type consistency:** `EnrichedListing` extends `Listing` and adds `tier`, `deal`, `searchId`. All components receiving `EnrichedListing` use those exact fields. `AppState.enrichedFor()` returns `EnrichedListing[]`. Dashboard spreads onto cards correctly.
