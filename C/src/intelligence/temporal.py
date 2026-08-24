"""Temporal organizational snapshots."""

import json
from datetime import datetime, timedelta
from collections import defaultdict

from src.models import database as db


class TemporalMemory:
    SNAPSHOT_DAYS = [1, 5, 10, 15, 20, 25, 30]

    def build_snapshots(self, base_date: str = "2026-07-22"):
        base = datetime.fromisoformat(base_date)
        events = db.query("SELECT * FROM organizational_events ORDER BY timestamp")
        projects = db.query("SELECT * FROM projects")
        blockers = db.query("SELECT * FROM blockers")

        for day_num in self.SNAPSHOT_DAYS:
            cutoff = (base + timedelta(days=day_num)).isoformat()
            day_events = [e for e in events if e["timestamp"] <= cutoff]
            active_blockers = [
                b for b in blockers
                if b["timestamp"] <= cutoff and (not b.get("resolved_at") or b["resolved_at"] > cutoff)
            ]

            project_states = {}
            for p in projects:
                proj_events = [e for e in day_events if e.get("project_id") == p["id"]]
                blockers_for_proj = [b for b in active_blockers if b.get("project_id") == p["id"]]
                status = p["status"]
                if blockers_for_proj:
                    status = "at_risk"
                project_states[p["id"]] = {
                    "name": p["name"],
                    "status": status,
                    "blockers": len(blockers_for_proj),
                    "recent_events": len(proj_events),
                }

            snapshot = {
                "date": cutoff[:10],
                "day_number": day_num,
                "events_count": len(day_events),
                "active_blockers": len(active_blockers),
                "projects": project_states,
                "recent_events": day_events[-10:],
            }
            db.insert_many("daily_snapshots", [{
                "snapshot_date": cutoff[:10],
                "data": json.dumps(snapshot),
            }])

    def get_snapshot(self, date: str) -> dict:
        row = db.query_one("SELECT data FROM daily_snapshots WHERE snapshot_date=?", (date,))
        if row:
            return json.loads(row["data"])
        return {}

    def get_events_in_range(self, start: str, end: str) -> list[dict]:
        return db.query(
            "SELECT * FROM organizational_events WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp",
            (start, end),
        )

    def what_changed_between(self, start_date: str, end_date: str) -> dict:
        events = self.get_events_in_range(start_date, end_date)
        by_type = defaultdict(list)
        for e in events:
            by_type[e.get("event_type", "update")].append(e)
        return {
            "period": f"{start_date} to {end_date}",
            "total_events": len(events),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "events": events,
        }
