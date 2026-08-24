"""Small SQLite index for workflow-friendly local persistence."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any


def build_database(data: dict[str, Any], path: str | Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("DROP TABLE IF EXISTS activities; CREATE TABLE activities (id INTEGER PRIMARY KEY, timestamp TEXT, employee TEXT, department TEXT, project TEXT, activity_type TEXT, content TEXT, related_task TEXT);")
    connection.executemany("INSERT INTO activities(timestamp, employee, department, project, activity_type, content, related_task) VALUES (?, ?, ?, ?, ?, ?, ?)", [(a["timestamp"], a["employee"], a["department"], a["project"], a["activity_type"], a["content"], a["related_task"]) for a in data["activities"]])
    connection.commit()
    connection.close()


def load_json_data(data_dir: str | Path) -> dict[str, Any]:
    directory = Path(data_dir)
    return {name: json.loads((directory / f"{name}.json").read_text(encoding="utf-8")) for name in ["company", "employees", "projects", "tasks", "activities"]}
