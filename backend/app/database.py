"""SQLite database for persistence - sessions, settings, logs."""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "focusai.db"


def get_conn():
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
    except sqlite3.OperationalError:
        import tempfile
        alt = Path(tempfile.gettempdir()) / "focusai.db"
        conn = sqlite3.connect(str(alt), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            focus_score INTEGER,
            productive_sec INTEGER DEFAULT 0,
            distracting_sec INTEGER DEFAULT 0,
            neutral_sec INTEGER DEFAULT 0,
            switch_count INTEGER DEFAULT 0,
            idle_sec INTEGER DEFAULT 0,
            top_apps TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS focus_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            timestamp TEXT,
            focus_score INTEGER,
            session_sec INTEGER
        );
        CREATE TABLE IF NOT EXISTS system_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message TEXT
        );
    """)
    conn.commit()
    conn.close()


def save_setting(key: str, value):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, json.dumps(value) if not isinstance(value, (str, int, float)) else str(value))
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if not row:
        return default
    val = row[0]
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def save_session_snapshot(data: dict):
    conn = get_conn()
    now = datetime.now().isoformat()
    date = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO focus_snapshots (date, timestamp, focus_score, session_sec) VALUES (?, ?, ?, ?)",
        (date, now, data.get("focus_score", 0), data.get("session_time_sec", 0))
    )
    conn.commit()
    conn.close()


def get_daily_focus(date: str = None):
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    rows = conn.execute(
        "SELECT focus_score, session_sec FROM focus_snapshots WHERE date = ? ORDER BY timestamp",
        (date,)
    ).fetchall()
    conn.close()
    return [{"score": r[0], "session_sec": r[1]} for r in rows]


def get_monthly_focus(days: int = 30):
    conn = get_conn()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT date, AVG(focus_score) as avg_score, MAX(session_sec) as max_sec
        FROM focus_snapshots WHERE date >= ?
        GROUP BY date ORDER BY date
    """, (since,)).fetchall()
    conn.close()
    return [{"date": r[0], "score": round(r[1] or 0), "session_sec": r[2] or 0} for r in rows]


def get_weekly_summary():
    conn = get_conn()
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date, AVG(focus_score) FROM focus_snapshots WHERE date >= ? GROUP BY date ORDER BY date",
        (since,)
    ).fetchall()
    conn.close()
    daily = [{"date": r[0], "avg_focus": round(r[1] or 0)} for r in rows]
    best = max(daily, key=lambda x: x["avg_focus"])["date"] if daily else None
    avg_focus = round(sum(d["avg_focus"] for d in daily) / len(daily)) if daily else 0
    return {"avg_focus": avg_focus, "best_day": best, "daily": daily}


def add_log(level: str, message: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO system_log (timestamp, level, message) VALUES (?, ?, ?)",
        (datetime.now().strftime("%H:%M:%S"), level, message)
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, level, message FROM system_log ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"time": r[0], "level": r[1], "msg": r[2]} for r in reversed(rows)]
