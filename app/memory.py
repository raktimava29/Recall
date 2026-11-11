import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import get_settings


class MemoryStore:
    """SQLite-backed, timestamped conversation memory."""

    def __init__(self, db_path: str | None = None, local_timezone: str | None = None):
        settings = get_settings()
        self.db_path = db_path or settings.database_path
        self.timezone_name = local_timezone or settings.local_timezone
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    created_at_local TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id, id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_utc ON messages(created_at_utc)")

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json"))
        return item

    def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> dict:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        now = datetime.now(timezone.utc)
        local = now.astimezone(ZoneInfo(self.timezone_name))
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO messages
                (session_id, role, content, created_at_utc, created_at_local, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, now.isoformat(), local.isoformat(),
                 json.dumps(metadata or {}, ensure_ascii=False)),
            )
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return self._row(row)

    def recent_messages(self, session_id: str, limit: int = 10) -> list[dict]:
        limit = max(1, min(int(limit), 50))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [self._row(row) for row in reversed(rows)]

    def search_memory(self, session_id: str, query: str, limit: int = 5) -> list[dict]:
        """Token-overlap retrieval; returns original messages and exact timestamps."""
        stop = {"what", "when", "where", "which", "have", "about", "from", "that",
                "this", "with", "were", "your", "yesterday", "today", "did"}
        tokens = list(dict.fromkeys(
            token.lower() for token in re.findall(r"[a-zA-Z0-9_'-]{3,}", query)
            if token.lower() not in stop
        ))
        if not tokens:
            return []
        tokens = tokens[:8]
        clauses = " OR ".join("content LIKE ?" for _ in tokens)
        params = [session_id, *[f"%{token}%" for token in tokens], max(1, min(limit, 10))]
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM messages WHERE session_id = ? AND ({clauses}) ORDER BY id DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    def list_sessions(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT session_id, MAX(created_at_utc) AS last_message_at, COUNT(*) AS message_count
                FROM messages GROUP BY session_id ORDER BY last_message_at DESC LIMIT ?
            """, (max(1, min(limit, 100)),)).fetchall()
        return [dict(row) for row in rows]

    def list_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        return self.recent_messages(session_id, limit)
