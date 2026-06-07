# models.py
import sqlite3
import uuid
from datetime import datetime

class Database:
    def __init__(self, path: str = "carfinder.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS searches (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                trim TEXT DEFAULT '',
                year INTEGER NOT NULL,
                max_price INTEGER NOT NULL,
                ideal_price INTEGER NOT NULL,
                max_miles INTEGER NOT NULL,
                ideal_miles INTEGER NOT NULL,
                zip TEXT NOT NULL,
                city TEXT NOT NULL,
                radius_miles INTEGER NOT NULL DEFAULT 300,
                interval_hours INTEGER NOT NULL DEFAULT 2,
                alert_emails TEXT NOT NULL DEFAULT '',
                trims TEXT NOT NULL DEFAULT '',
                drivetrain TEXT NOT NULL DEFAULT 'Any',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS listings (
                id TEXT NOT NULL,
                search_id TEXT NOT NULL,
                title TEXT,
                price INTEGER,
                miles INTEGER,
                city TEXT,
                state TEXT,
                distance REAL,
                source TEXT,
                url TEXT,
                market INTEGER,
                drivetrain TEXT,
                exterior TEXT,
                interior TEXT,
                owners INTEGER,
                accidents INTEGER,
                days_listed INTEGER,
                photos INTEGER,
                seller_type TEXT,
                seller_name TEXT,
                seller_rating REAL,
                vin TEXT,
                drop_amount INTEGER,
                drop_when TEXT,
                is_new INTEGER DEFAULT 1,
                first_seen TEXT,
                last_seen TEXT,
                PRIMARY KEY (id, search_id),
                FOREIGN KEY (search_id) REFERENCES searches(id)
            );

            CREATE TABLE IF NOT EXISTS saved_listings (
                user_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                PRIMARY KEY (user_id, listing_id)
            );

            CREATE TABLE IF NOT EXISTS hidden_listings (
                user_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                hidden_at TEXT NOT NULL,
                PRIMARY KEY (user_id, listing_id)
            );
        """)
        self.conn.commit()
        # Migrate: alert_email → alert_emails for existing DBs
        try:
            self.conn.execute("ALTER TABLE searches ADD COLUMN alert_emails TEXT NOT NULL DEFAULT ''")
            self.conn.execute("UPDATE searches SET alert_emails = alert_email WHERE alert_emails = ''")
            self.conn.commit()
        except Exception:
            pass  # Column already exists
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
        # Copy existing single trim value into trims column
        try:
            self.conn.execute(
                "UPDATE searches SET trims = trim WHERE trims = '' AND trim != ''"
            )
            self.conn.commit()
        except Exception:
            pass

    def _row_to_dict(self, row) -> dict:
        return dict(row) if row else None

    # ── Searches ──────────────────────────────────────────────────────────

    def create_search(self, data: dict) -> dict:
        search_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
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
        self.conn.commit()
        return self.get_search(search_id)

    def get_search(self, search_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM searches WHERE id = ?", (search_id,)
        ).fetchone()
        return self._row_to_dict(row)

    def list_searches(self, user_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM searches WHERE user_id = ? AND active = 1 ORDER BY created_at",
            (user_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def list_all_active_searches(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM searches WHERE active = 1"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_search(self, search_id: str, data: dict) -> dict:
        fields = ["make", "model", "trim", "year", "max_price", "ideal_price",
                  "max_miles", "ideal_miles", "zip", "city", "radius_miles",
                  "interval_hours", "alert_emails", "trims", "drivetrain"]
        sets = ", ".join(f"{f} = ?" for f in fields if f in data)
        vals = [data[f] for f in fields if f in data] + [search_id]
        if sets:
            self.conn.execute(f"UPDATE searches SET {sets} WHERE id = ?", vals)
            self.conn.commit()
        return self.get_search(search_id)

    def delete_search(self, search_id: str) -> None:
        self.conn.execute(
            "UPDATE searches SET active = 0 WHERE id = ?", (search_id,)
        )
        self.conn.commit()

    # ── Listings ──────────────────────────────────────────────────────────

    def upsert_listing(self, listing: dict) -> None:
        now = datetime.now().isoformat()
        existing = self.conn.execute(
            "SELECT id FROM listings WHERE id = ? AND search_id = ?",
            (listing["id"], listing["search_id"])
        ).fetchone()
        if existing:
            self.conn.execute("""
                UPDATE listings SET price=?, miles=?, days_listed=?, is_new=?,
                drop_amount=?, drop_when=?, last_seen=?
                WHERE id=? AND search_id=?
            """, (listing["price"], listing["miles"], listing.get("days_listed"),
                  listing.get("is_new", 0), listing.get("drop_amount"),
                  listing.get("drop_when"), now,
                  listing["id"], listing["search_id"]))
        else:
            self.conn.execute("""
                INSERT INTO listings
                (id, search_id, title, price, miles, city, state, distance,
                 source, url, market, drivetrain, exterior, interior, owners,
                 accidents, days_listed, photos, seller_type, seller_name,
                 seller_rating, vin, drop_amount, drop_when, is_new,
                 first_seen, last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (listing["id"], listing["search_id"], listing.get("title"),
                  listing.get("price"), listing.get("miles"), listing.get("city"),
                  listing.get("state"), listing.get("distance"), listing.get("source"),
                  listing.get("url"), listing.get("market"), listing.get("drivetrain"),
                  listing.get("exterior"), listing.get("interior"), listing.get("owners"),
                  listing.get("accidents"), listing.get("days_listed"), listing.get("photos"),
                  listing.get("seller_type"), listing.get("seller_name"),
                  listing.get("seller_rating"), listing.get("vin"),
                  listing.get("drop_amount"), listing.get("drop_when"),
                  listing.get("is_new", 1), now, now))
        self.conn.commit()

    def get_listings(self, search_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM listings WHERE search_id = ? ORDER BY price ASC",
            (search_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def mark_all_seen(self, search_id: str) -> None:
        self.conn.execute(
            "UPDATE listings SET is_new = 0 WHERE search_id = ?", (search_id,)
        )
        self.conn.commit()

    # ── Save / Hide ───────────────────────────────────────────────────────

    def save_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO saved_listings (user_id, listing_id, saved_at) VALUES (?,?,?)",
            (user_id, listing_id, datetime.now().isoformat())
        )
        self.conn.commit()

    def unsave_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "DELETE FROM saved_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        )
        self.conn.commit()

    def is_saved(self, user_id: str, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM saved_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        ).fetchone()
        return row is not None

    def get_saved_ids(self, user_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT listing_id FROM saved_listings WHERE user_id=?", (user_id,)
        ).fetchall()
        return [r["listing_id"] for r in rows]

    def hide_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO hidden_listings (user_id, listing_id, hidden_at) VALUES (?,?,?)",
            (user_id, listing_id, datetime.now().isoformat())
        )
        self.conn.commit()

    def unhide_listing(self, user_id: str, listing_id: str) -> None:
        self.conn.execute(
            "DELETE FROM hidden_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        )
        self.conn.commit()

    def is_hidden(self, user_id: str, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM hidden_listings WHERE user_id=? AND listing_id=?",
            (user_id, listing_id)
        ).fetchone()
        return row is not None

    def get_hidden_ids(self, user_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT listing_id FROM hidden_listings WHERE user_id=?", (user_id,)
        ).fetchall()
        return [r["listing_id"] for r in rows]

    def close(self):
        self.conn.close()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()
