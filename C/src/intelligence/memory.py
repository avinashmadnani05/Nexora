"""Organizational memory storage and retrieval."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.models import database as db


class OrganizationalMemory:
    def load_organization(self, org_data: dict):
        db.insert_many("employees", org_data.get("employees", []), ["skills"])
        db.insert_many("departments", org_data.get("departments", []))
        db.insert_many("teams", org_data.get("teams", []))
        db.insert_many("projects", org_data.get("projects", []), ["members"])
        db.insert_many("tasks", org_data.get("tasks", []))

    def store_raw_communications(self, comms: list[dict]):
        db.insert_many("raw_communications", comms, ["recipients", "metadata"])

    def store_events(self, events: list[dict]):
        rows = []
        for e in events:
            rows.append({
                "id": e.get("id", f"EVT-{uuid.uuid4().hex[:8]}"),
                "event_type": e.get("event_type"),
                "timestamp": e.get("timestamp"),
                "person": e.get("person"),
                "department": e.get("department"),
                "project_id": e.get("project_id"),
                "task_id": e.get("task_id"),
                "summary": e.get("summary"),
                "status": e.get("status"),
                "dependency": e.get("dependency"),
                "confidence": e.get("confidence", 0.7),
                "source_type": e.get("source_type"),
                "source_id": e.get("source_id"),
                "metadata": json.dumps(e.get("metadata", {})),
            })
        db.insert_many("organizational_events", rows)

        for e in events:
            if e.get("event_type") == "blocker":
                db.insert_many("blockers", [{
                    "id": f"BLK-{uuid.uuid4().hex[:8]}",
                    "timestamp": e.get("timestamp"),
                    "resolved_at": None,
                    "summary": e.get("summary"),
                    "project_id": e.get("project_id"),
                    "task_id": e.get("task_id"),
                    "dependency": e.get("dependency"),
                    "person": e.get("person"),
                    "status": "active",
                    "source_ids": json.dumps([e.get("source_id")]),
                }])
            if e.get("event_type") == "decision":
                db.insert_many("decisions", [{
                    "id": f"DEC-{uuid.uuid4().hex[:8]}",
                    "timestamp": e.get("timestamp"),
                    "summary": e.get("summary"),
                    "department": e.get("department"),
                    "project_id": e.get("project_id"),
                    "participants": json.dumps([e.get("person")]),
                    "source_ids": json.dumps([e.get("source_id")]),
                    "confidence": e.get("confidence", 0.8),
                }])
            if e.get("event_type") == "resolution" and e.get("dependency"):
                db.query(
                    "UPDATE blockers SET status='resolved', resolved_at=? WHERE dependency=? AND status='active'",
                    (e.get("timestamp"), e.get("dependency")),
                )

    def store_meetings(self, meetings: list[dict]):
        rows = [{
            "id": m["id"],
            "date": m.get("date"),
            "participants": json.dumps(m.get("participants", [])),
            "department": m.get("department"),
            "project_id": m.get("project_id"),
            "transcript": m.get("transcript"),
            "summary": m.get("transcript", "")[:300],
        } for m in meetings]
        db.insert_many("meetings", rows)

    def get_employees(self, department: Optional[str] = None) -> list[dict]:
        if department:
            return db.query("SELECT * FROM employees WHERE department=?", (department,))
        return db.query("SELECT * FROM employees")

    def get_projects(self, department: Optional[str] = None) -> list[dict]:
        if department:
            return db.query("SELECT * FROM projects WHERE department=?", (department,))
        return db.query("SELECT * FROM projects")

    def get_tasks(self, status: Optional[str] = None) -> list[dict]:
        if status:
            return db.query("SELECT * FROM tasks WHERE status=?", (status,))
        return db.query("SELECT * FROM tasks")

    def get_events(
        self,
        department: Optional[str] = None,
        project_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM organizational_events WHERE 1=1"
        params = []
        if department:
            sql += " AND department=?"
            params.append(department)
        if project_id:
            sql += " AND project_id=?"
            params.append(project_id)
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        if since:
            sql += " AND timestamp>=?"
            params.append(since)
        if until:
            sql += " AND timestamp<=?"
            params.append(until)
        sql += " ORDER BY timestamp"
        return db.query(sql, tuple(params))

    def get_blockers(self, active_only: bool = True) -> list[dict]:
        if active_only:
            return db.query("SELECT * FROM blockers WHERE status='active'")
        return db.query("SELECT * FROM blockers")

    def get_decisions(self, department: Optional[str] = None) -> list[dict]:
        if department:
            return db.query("SELECT * FROM decisions WHERE department=?", (department,))
        return db.query("SELECT * FROM decisions")

    def search_communications(self, query_text: str, limit: int = 20) -> list[dict]:
        pattern = f"%{query_text}%"
        return db.query(
            "SELECT * FROM raw_communications WHERE content LIKE ? OR subject LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (pattern, pattern, limit),
        )

    def get_communications_for_project(self, project_id: str) -> list[dict]:
        return db.query(
            "SELECT * FROM raw_communications WHERE project_id=? ORDER BY timestamp",
            (project_id,),
        )

    def get_project_by_name(self, name: str) -> Optional[dict]:
        return db.query_one("SELECT * FROM projects WHERE name LIKE ?", (f"%{name}%",))

    def get_employee_by_name(self, name: str) -> Optional[dict]:
        return db.query_one("SELECT * FROM employees WHERE name LIKE ?", (f"%{name}%",))
