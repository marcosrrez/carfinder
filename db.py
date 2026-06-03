import sqlite3


class ListingDB:
    def __init__(self, path: str = "carfinder.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)"
        )
        self.conn.commit()

    def is_new(self, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM seen WHERE id = ?", (listing_id,)
        ).fetchone()
        return row is None

    def mark_seen(self, listing_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen (id) VALUES (?)", (listing_id,)
        )
        self.conn.commit()

    def filter_new(self, listings: list[dict]) -> list[dict]:
        new = [l for l in listings if self.is_new(l["id"])]
        for l in new:
            self.mark_seen(l["id"])
        return new
