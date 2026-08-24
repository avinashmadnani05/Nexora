"""SQLite database schema and operations."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.utils.config import DATABASE_DIR, get_config


def get_db_path() -> Path:
    url = get_config()["database_url"]
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "")
        return Path(path)
    return DATABASE_DIR / "nexora.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    team TEXT,
    role TEXT,
    manager TEXT,
    skills TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    owner TEXT,
    members TEXT,
    status TEXT,
    progress REAL DEFAULT 0,
    start_date TEXT,
    deadline TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT,
    assignee TEXT,
    status TEXT,
    priority TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS raw_communications (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    sender TEXT,
    recipients TEXT,
    channel TEXT,
    subject TEXT,
    content TEXT,
    department TEXT,
    project_id TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS organizational_events (
    id TEXT PRIMARY KEY,
    event_type TEXT,
    timestamp TEXT,
    person TEXT,
    department TEXT,
    project_id TEXT,
    task_id TEXT,
    summary TEXT,
    status TEXT,
    dependency TEXT,
    confidence REAL,
    source_type TEXT,
    source_id TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    timestamp TEXT,
    summary TEXT,
    department TEXT,
    project_id TEXT,
    participants TEXT,
    source_ids TEXT,
    confidence REAL
);

CREATE TABLE IF NOT EXISTS blockers (
    id TEXT PRIMARY KEY,
    timestamp TEXT,
    resolved_at TEXT,
    summary TEXT,
    project_id TEXT,
    task_id TEXT,
    dependency TEXT,
    person TEXT,
    status TEXT,
    source_ids TEXT
);

CREATE TABLE IF NOT EXISTS dependencies (
    id TEXT PRIMARY KEY,
    from_entity TEXT,
    to_entity TEXT,
    relation_type TEXT,
    project_id TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    date TEXT,
    participants TEXT,
    department TEXT,
    project_id TEXT,
    transcript TEXT,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS daily_snapshots (
    snapshot_date TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_briefs (
    brief_date TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    generated_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    actor TEXT,
    action TEXT,
    details TEXT
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def clear_all_data():
    tables = [
        "employees", "departments", "teams", "projects", "tasks",
        "raw_communications", "organizational_events", "decisions",
        "blockers", "dependencies", "meetings", "daily_snapshots",
        "daily_briefs", "audit_log",
    ]
    with get_connection() as conn:
        for t in tables:
            conn.execute(f"DELETE FROM {t}")


def insert_many(table: str, rows: list[dict], json_fields: Optional[list[str]] = None):
    if not rows:
        return
    json_fields = json_fields or []
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" * len(cols))
    col_names = ", ".join(cols)
    sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
    with get_connection() as conn:
        for row in rows:
            values = []
            for c in cols:
                v = row[c]
                if c in json_fields and v is not None and not isinstance(v, str):
                    v = json.dumps(v)
                values.append(v)
            conn.execute(sql, values)


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    rows = query(sql, params)
    return rows[0] if rows else None


def log_audit(actor: str, action: str, details: dict):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, actor, action, details) VALUES (?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), actor, action, json.dumps(details)),
        )
