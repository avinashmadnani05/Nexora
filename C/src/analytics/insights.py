"""Organizational analytics and insights."""

from collections import Counter, defaultdict

from src.intelligence.memory import OrganizationalMemory
from src.models import database as db


def get_org_overview() -> dict:
    memory = OrganizationalMemory()
    employees = memory.get_employees()
    projects = memory.get_projects()
    tasks = memory.get_tasks()
    blockers = memory.get_blockers()

    blocked_tasks = [t for t in tasks if t.get("status") == "blocked"]
    at_risk = []
    for p in projects:
        proj_blockers = [b for b in blockers if b.get("project_id") == p["id"]]
        if proj_blockers:
            at_risk.append({**p, "blocker_count": len(proj_blockers)})

    return {
        "employee_count": len(employees),
        "department_count": len(set(e["department"] for e in employees)),
        "project_count": len(projects),
        "active_tasks": len([t for t in tasks if t.get("status") in ("open", "in_progress")]),
        "blocked_tasks": len(blocked_tasks),
        "projects_at_risk": at_risk,
        "active_blockers": len(blockers),
    }


def get_department_insights(department: str) -> dict:
    memory = OrganizationalMemory()
    events = memory.get_events(department=department)
    projects = memory.get_projects(department=department)
    blockers = [b for b in memory.get_blockers(active_only=False) if department.lower() in str(b).lower()]

    by_type = Counter(e.get("event_type") for e in events)
    return {
        "department": department,
        "projects": len(projects),
        "events": len(events),
        "blockers": len(blockers),
        "event_breakdown": dict(by_type),
        "recent_events": events[-5:],
    }


def get_ai_insights() -> dict:
    memory = OrganizationalMemory()
    events = db.query("SELECT * FROM organizational_events")
    blockers = memory.get_blockers(active_only=False)
    decisions = memory.get_decisions()

    duplicate = [e for e in events if e.get("event_type") == "duplicate_work"]
    knowledge_risk = [e for e in events if "single point" in str(e.get("summary", "")).lower() or "only" in str(e.get("summary", "")).lower()]

    person_mentions = Counter(e.get("person") for e in events if e.get("person"))
    knowledge_concentration = [
        {"person": p, "mentions": c}
        for p, c in person_mentions.most_common(5)
        if c >= 3
    ]

    return {
        "blockers": blockers[:10],
        "decisions": decisions[:10],
        "duplicate_work": duplicate,
        "knowledge_concentration": knowledge_concentration,
        "knowledge_risks": knowledge_risk[:5],
        "risks": [e for e in events if e.get("event_type") in ("risk", "blocker")][:10],
    }


def get_work_involvement_signals(employee_id: str) -> dict:
    emp = db.query_one("SELECT name FROM employees WHERE id=?", (employee_id,))
    name = emp["name"] if emp else employee_id
    events = db.query("SELECT * FROM organizational_events WHERE person LIKE ?", (f"%{name}%",))
    comms = db.query("SELECT * FROM raw_communications WHERE sender=? LIMIT 20", (employee_id,))
    collaborators = Counter()
    for c in comms:
        if c.get("department"):
            collaborators[c["department"]] += 1
    return {
        "communication_count": len(comms),
        "event_count": len(events),
        "recent_events": events[-5:],
        "department_activity": dict(collaborators),
    }
