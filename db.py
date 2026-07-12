"""SQLite persistence for Wear Calendar MVP."""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

DATA_DIR = Path(os.environ.get("WEAR_DATA_DIR", Path(__file__).resolve().parent / "data"))
DB_PATH = Path(os.environ.get("WEAR_DB_PATH", DATA_DIR / "wear.db"))


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_password(password, salt), stored)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                type TEXT,
                photo_path TEXT,
                last_washed_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wear_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                worn_on TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, item_id, worn_on)
            );
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                props TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        cols = {r[1] for r in conn.execute("PRAGMA table_info(items)").fetchall()}
        if "photo_path" not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN photo_path TEXT")


def track(conn: sqlite3.Connection, name: str, user_id: Optional[int] = None, props: str = "") -> None:
    conn.execute(
        "INSERT INTO analytics_events (user_id, name, props, created_at) VALUES (?, ?, ?, ?)",
        (user_id, name, props, datetime.utcnow().isoformat()),
    )


def create_user(email: str, password: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.lower().strip(), _hash_password(password), datetime.utcnow().isoformat()),
        )
        track(conn, "signup_success", cur.lastrowid, "method=password")
        return int(cur.lastrowid)


def authenticate(email: str, password: str) -> Optional[sqlite3.Row]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return row
        return None


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()


def list_items(user_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT * FROM items WHERE user_id = ?
            ORDER BY type COLLATE NOCASE, name COLLATE NOCASE
            """,
            (user_id,),
        ).fetchall()


def create_item(
    user_id: int,
    name: str,
    type_: str,
    photo_path: Optional[str] = None,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO items (user_id, name, type, photo_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                type_.strip(),
                photo_path,
                datetime.utcnow().isoformat(),
            ),
        )
        track(
            conn,
            "item_create",
            user_id,
            f"has_photo={1 if photo_path else 0}&type={type_.strip()}",
        )
        return int(cur.lastrowid)


def update_item(
    user_id: int,
    item_id: int,
    name: str,
    type_: str,
    photo_path: Optional[str] = None,
    clear_photo: bool = False,
) -> bool:
    with connect() as conn:
        item = conn.execute(
            "SELECT photo_path FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()
        if not item:
            return False
        new_photo = item["photo_path"]
        if clear_photo:
            new_photo = None
        elif photo_path:
            new_photo = photo_path
        cur = conn.execute(
            """
            UPDATE items SET name = ?, type = ?, photo_path = ?
            WHERE id = ? AND user_id = ?
            """,
            (name.strip(), type_.strip(), new_photo, item_id, user_id),
        )
        return cur.rowcount > 0


def get_item(user_id: int, item_id: int) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()


def delete_item(user_id: int, item_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM items WHERE id = ? AND user_id = ?", (item_id, user_id))
        return cur.rowcount > 0


def log_wears(user_id: int, worn_on: str, item_ids: list[int]) -> int:
    now = datetime.utcnow().isoformat()
    count = 0
    with connect() as conn:
        for item_id in item_ids:
            owned = conn.execute(
                "SELECT id FROM items WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            ).fetchone()
            if not owned:
                continue
            try:
                conn.execute(
                    "INSERT INTO wear_events (user_id, item_id, worn_on, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, item_id, worn_on, now),
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        track(conn, "wear_log_create", user_id, f"item_count={count}&date={worn_on}")
    return count


def delete_wear(user_id: int, wear_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM wear_events WHERE id = ? AND user_id = ?",
            (wear_id, user_id),
        )
        if cur.rowcount:
            track(conn, "wear_log_delete", user_id)
        return cur.rowcount > 0


def wears_for_range(user_id: int, start: str, end: str) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT w.id AS wear_id, w.worn_on, w.item_id, i.name, i.type, i.photo_path
            FROM wear_events w
            JOIN items i ON i.id = w.item_id
            WHERE w.user_id = ? AND w.worn_on >= ? AND w.worn_on <= ?
            ORDER BY w.worn_on, i.type COLLATE NOCASE, i.name COLLATE NOCASE
            """,
            (user_id, start, end),
        ).fetchall()


def item_wear_history(user_id: int, item_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, worn_on FROM wear_events
            WHERE user_id = ? AND item_id = ?
            ORDER BY worn_on DESC
            """,
            (user_id, item_id),
        ).fetchall()


def wears_since_wash(user_id: int, item_id: int) -> int:
    with connect() as conn:
        item = conn.execute(
            "SELECT last_washed_at FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()
        if not item:
            return 0
        if item["last_washed_at"]:
            row = conn.execute(
                """
                SELECT COUNT(*) AS c FROM wear_events
                WHERE user_id = ? AND item_id = ? AND created_at > ?
                """,
                (user_id, item_id, item["last_washed_at"]),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM wear_events WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            ).fetchone()
        return int(row["c"])


def mark_washed(user_id: int, item_id: int) -> bool:
    with connect() as conn:
        item = conn.execute(
            "SELECT id, last_washed_at FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()
        if not item:
            return False
        if item["last_washed_at"]:
            before = conn.execute(
                """
                SELECT COUNT(*) AS c FROM wear_events
                WHERE user_id = ? AND item_id = ? AND created_at > ?
                """,
                (user_id, item_id, item["last_washed_at"]),
            ).fetchone()["c"]
        else:
            before = conn.execute(
                "SELECT COUNT(*) AS c FROM wear_events WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            ).fetchone()["c"]
        cur = conn.execute(
            "UPDATE items SET last_washed_at = ? WHERE id = ? AND user_id = ?",
            (datetime.utcnow().isoformat(), item_id, user_id),
        )
        if cur.rowcount:
            track(conn, "wash_mark", user_id, f"wears_since_wash_before={before}")
        return cur.rowcount > 0


def most_worn(user_id: int, days: int = 7) -> list[dict[str, Any]]:
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    end = date.today().isoformat()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT i.id, i.name, i.type, i.photo_path, COUNT(*) AS wear_count
            FROM wear_events w
            JOIN items i ON i.id = w.item_id
            WHERE w.user_id = ? AND w.worn_on >= ? AND w.worn_on <= ?
            GROUP BY i.id
            ORDER BY wear_count DESC, i.type COLLATE NOCASE, i.name COLLATE NOCASE
            """,
            (user_id, start, end),
        ).fetchall()
        track(conn, "most_worn_view", user_id, f"range_days={days}")
        return [dict(r) for r in rows]


def track_view(user_id: int, name: str, props: str = "") -> None:
    with connect() as conn:
        track(conn, name, user_id, props)
