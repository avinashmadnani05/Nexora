"""Daily organizational briefing generation."""

from datetime import datetime, timedelta

from src.intelligence.memory import OrganizationalMemory
from src.models import database as db


def generate_daily_brief(date: str = None) -> str:
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    memory = OrganizationalMemory()

    start = (datetime.fromisoformat(date) - timedelta(days=1)).isoformat()
    end = f"{date}T23:59:59"

    events = memory.get_events(since=start, until=end)
    if not events:
        events = db.query("SELECT * FROM organizational_events ORDER BY timestamp DESC LIMIT 50")

    blockers = memory.get_blockers()
    departments = ["Engineering", "Marketing", "HR", "Product", "Sales", "Finance"]

    lines = [f"NEXORA — DAILY BRIEF", f"{date}", ""]

    risks = []
    for dept in departments:
        dept_events = [e for e in events if e.get("department") == dept]
        dept_blockers = [b for b in blockers if b.get("summary") and dept.lower() in str(b).lower()]
        dept_blocker_events = [e for e in dept_events if e.get("event_type") == "blocker"]
        completed = [e for e in dept_events if e.get("event_type") == "resolution"]

        lines.append(dept.upper())
        if dept_blocker_events:
            lines.append(f"• {dept_blocker_events[0].get('summary', 'Blocker detected')[:80]}")
            risks.append(dept_blocker_events[0].get("summary", "")[:80])
        elif dept_events:
            lines.append(f"• {dept_events[-1].get('summary', 'Activity detected')[:80]}")
        else:
            lines.append("• No significant signals in recent data.")
        if completed:
            lines.append(f"• {len(completed)} resolution(s) recorded.")
        if dept_blocker_events:
            lines.append(f"• {len(dept_blocker_events)} blocker(s) detected.")
        lines.append("")

    lines.append("TOP RISKS")
    seen = set()
    risk_items = []
    for b in blockers[:5]:
        s = b.get("summary", b.get("dependency", ""))[:80]
        if s and s not in seen:
            risk_items.append(s)
            seen.add(s)
    for r in risks:
        if r not in seen:
            risk_items.append(r)
            seen.add(r)
    for i, r in enumerate(risk_items[:5], 1):
        lines.append(f"{i}. {r}")

    content = "\n".join(lines)
    db.insert_many("daily_briefs", [{
        "brief_date": date,
        "content": content,
        "generated_at": datetime.utcnow().isoformat(),
    }])
    return content
