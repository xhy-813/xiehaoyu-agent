"""会话与消息的 SQLite 持久化（设计文档 §4 存储实现选型）。

同步 ``sqlite3`` + ``threading.Lock`` + WAL。公开函数均为同步阻塞实现；
async 调用方（routers/services）必须用 ``asyncio.to_thread()`` 包装，
避免阻塞 FastAPI 事件循环。
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path

_DB_PATH = Path(os.getenv("SESSIONS_DB_PATH", "data/sessions.db"))

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id           TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL,
  title        TEXT,
  summary      TEXT,
  summary_upto INTEGER DEFAULT 0,
  created_at   TIMESTAMP NOT NULL,
  updated_at   TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id    TEXT NOT NULL,
  role          TEXT NOT NULL,
  content       TEXT NOT NULL,
  artifacts_json TEXT,
  created_at    TIMESTAMP NOT NULL,
  FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
"""


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _days_ago(days: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400))


def init_store(path: Path | None = None) -> None:
    """Open (creating if needed) the sessions DB.  Idempotent.

    App 启动时由 lifespan 显式调用；未调用时首次使用自动按默认路径初始化。
    """
    global _conn
    with _lock:
        if _conn is not None:
            return
        db_path = Path(path) if path is not None else _DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA)
        conn.commit()
        _conn = conn


def close_store() -> None:
    """Close the connection (tests use this between fixtures)."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None


def _c() -> sqlite3.Connection:
    if _conn is None:
        init_store()
    assert _conn is not None
    return _conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


# ── sessions ────────────────────────────────────────────────


def create_session(user_id: str) -> str:
    sid = str(uuid.uuid4())
    now = _now()
    with _lock:
        _c().execute(
            "INSERT INTO sessions (id, user_id, title, summary, summary_upto, created_at, updated_at)"
            " VALUES (?, ?, NULL, NULL, 0, ?, ?)",
            (sid, user_id, now, now),
        )
        _c().commit()
    return sid


def get_session(session_id: str) -> dict | None:
    row = _c().execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_sessions(user_id: str) -> list[dict]:
    rows = _c().execute(
        "SELECT id, title, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def rename_session(session_id: str, title: str) -> None:
    """Set/rename title.  不触碰 updated_at（重命名不是聊天活动，不应改变列表排序）。"""
    with _lock:
        _c().execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
        _c().commit()


def delete_session(session_id: str) -> None:
    with _lock:
        _c().execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        _c().commit()


def search_sessions(user_id: str, q: str) -> list[dict]:
    pattern = f"%{q}%"
    rows = _c().execute(
        """
        SELECT DISTINCT s.id, s.title, s.updated_at
        FROM sessions s LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.user_id = ? AND (s.title LIKE ? OR m.content LIKE ?)
        ORDER BY s.updated_at DESC
        """,
        (user_id, pattern, pattern),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── messages ────────────────────────────────────────────────


def append_message(
    session_id: str, role: str, content: str, artifacts_json: str | None = None
) -> int:
    now = _now()
    with _lock:
        cur = _c().execute(
            "INSERT INTO messages (session_id, role, content, artifacts_json, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, artifacts_json, now),
        )
        _c().execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        _c().commit()
    return cur.lastrowid


def list_messages(session_id: str) -> list[dict]:
    rows = _c().execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def list_messages_after(session_id: str, after_id: int) -> list[dict]:
    rows = _c().execute(
        "SELECT * FROM messages WHERE session_id = ? AND id > ? ORDER BY id ASC",
        (session_id, after_id),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def count_turns(session_id: str) -> int:
    row = _c().execute(
        "SELECT COUNT(*) AS c FROM messages WHERE session_id = ?", (session_id,)
    ).fetchone()
    return row["c"] // 2


def count_new_turns(session_id: str, summary_upto: int) -> int:
    row = _c().execute(
        "SELECT COUNT(*) AS c FROM messages WHERE session_id = ? AND id > ?",
        (session_id, summary_upto),
    ).fetchone()
    return row["c"] // 2


# ── memory ──────────────────────────────────────────────────


def get_memory_context(session_id: str, recent_turns: int) -> dict:
    """Return {summary, summary_upto, recent}; recent 为最近 recent_turns 轮，时间正序。"""
    sess = get_session(session_id)
    if sess is None:
        return {"summary": "", "summary_upto": 0, "recent": []}
    rows = _c().execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, recent_turns * 2),
    ).fetchall()
    recent = [_row_to_dict(r) for r in reversed(rows)]
    return {
        "summary": sess["summary"] or "",
        "summary_upto": sess["summary_upto"] or 0,
        "recent": recent,
    }


def update_summary(session_id: str, summary: str, summary_upto: int) -> None:
    with _lock:
        _c().execute(
            "UPDATE sessions SET summary = ?, summary_upto = ? WHERE id = ?",
            (summary, summary_upto, session_id),
        )
        _c().commit()


# ── cleanup ─────────────────────────────────────────────────


def cleanup(max_age_days: int, max_per_user: int) -> dict:
    """删除过期会话 + 每用户超出 max_per_user 的最老会话。"""
    cutoff = _days_ago(max_age_days)
    with _lock:
        aged = _c().execute(
            "DELETE FROM sessions WHERE updated_at < ?", (cutoff,)
        ).rowcount
        overflow = 0
        rows = _c().execute(
            "SELECT user_id, COUNT(*) AS c FROM sessions GROUP BY user_id HAVING c > ?",
            (max_per_user,),
        ).fetchall()
        for r in rows:
            keep = _c().execute(
                "SELECT id FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (r["user_id"], max_per_user),
            ).fetchall()
            keep_ids = [k["id"] for k in keep]
            placeholders = ",".join("?" for _ in keep_ids)
            overflow += _c().execute(
                f"DELETE FROM sessions WHERE user_id = ? AND id NOT IN ({placeholders})",
                (r["user_id"], *keep_ids),
            ).rowcount
        _c().commit()
    return {"aged_out": aged, "overflow_deleted": overflow}