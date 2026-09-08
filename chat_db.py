# ─────────────────────────────────────────────────
#  KIRA — SQLite Chat History & Logs
#
#  Persists all conversations, routing events, and
#  agent actions to a local SQLite database.
#  Provides search over past conversations.
# ─────────────────────────────────────────────────
import sqlite3
import datetime
import threading
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "kira_data.db"

class ChatDB:
    """Thread-safe SQLite wrapper for Kira's persistent storage."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self._db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """One connection per thread (SQLite requirement)."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_schema(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                timestamp   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS routing_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    DEFAULT (datetime('now')),
                backend     TEXT,
                cpu_pct     REAL,
                ram_pct     REAL,
                latency_ms  REAL,
                reason      TEXT
            );

            CREATE TABLE IF NOT EXISTS action_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    DEFAULT (datetime('now')),
                task_goal   TEXT,
                step_num    INTEGER,
                action      TEXT,
                target      TEXT,
                value       TEXT,
                success     BOOLEAN
            );

            CREATE TABLE IF NOT EXISTS benchmark_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    DEFAULT (datetime('now')),
                prompt_id   INTEGER,
                prompt_text TEXT,
                backend     TEXT,
                latency_ms  REAL,
                tokens_out  INTEGER,
                tokens_per_sec REAL,
                response    TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
            CREATE INDEX IF NOT EXISTS idx_chat_ts ON chat_history(timestamp);
            CREATE INDEX IF NOT EXISTS idx_routing_ts ON routing_log(timestamp);
        """)
        conn.commit()

    # ── Chat History ─────────────────────────────

    def save_message(self, session_id: str, role: str, content: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()

    def get_session_messages(self, session_id: str, limit: int = 50) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT role, content, timestamp FROM chat_history "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def search_messages(self, query: str, limit: int = 20) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT session_id, role, content, timestamp FROM chat_history "
            "WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_sessions(self, limit: int = 20) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT session_id, MIN(timestamp) as started, MAX(timestamp) as last_msg, "
            "COUNT(*) as msg_count "
            "FROM chat_history GROUP BY session_id "
            "ORDER BY last_msg DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Routing Log ──────────────────────────────

    def log_routing(self, backend: str, cpu: float, ram: float,
                    latency_ms: float, reason: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO routing_log (backend, cpu_pct, ram_pct, latency_ms, reason) "
            "VALUES (?, ?, ?, ?, ?)",
            (backend, cpu, ram, latency_ms, reason)
        )
        conn.commit()

    def get_routing_history(self, limit: int = 100) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM routing_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ── Action Log ───────────────────────────────

    def log_action(self, task_goal: str, step_num: int, action: str,
                   target: str, value: str, success: bool):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO action_log (task_goal, step_num, action, target, value, success) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task_goal, step_num, action, target, value, success)
        )
        conn.commit()

    # ── Benchmark Results ────────────────────────

    def save_benchmark(self, prompt_id: int, prompt_text: str, backend: str,
                       latency_ms: float, tokens_out: int, tokens_per_sec: float,
                       response: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO benchmark_results "
            "(prompt_id, prompt_text, backend, latency_ms, tokens_out, tokens_per_sec, response) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (prompt_id, prompt_text, backend, latency_ms, tokens_out, tokens_per_sec, response)
        )
        conn.commit()

    def get_benchmark_results(self, limit: int = 50) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM benchmark_results ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def export_benchmarks_csv(self) -> str:
        """Returns benchmark results as CSV string."""
        rows = self.get_benchmark_results(limit=1000)
        if not rows:
            return "No benchmark data"
        
        headers = ["timestamp", "prompt_id", "prompt_text", "backend",
                    "latency_ms", "tokens_out", "tokens_per_sec"]
        lines = [",".join(headers)]
        for r in rows:
            line = ",".join(str(r.get(h, "")) for h in headers)
            lines.append(line)
        return "\n".join(lines)


# ── Singleton ────────────────────────────────────
chat_db = ChatDB()
