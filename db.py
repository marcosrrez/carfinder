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
        new = [listing for listing in listings if self.is_new(listing["id"])]
        for listing in new:
            self.mark_seen(listing["id"])
        return new

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
