"""Deterministic synthetic organization and activity generation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import random
from typing import Any

from .database import build_database

DEPARTMENTS = ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance"]
BASE_DATE = datetime(2026, 7, 23, 9, 0, tzinfo=timezone.utc)


def _employee_catalog() -> list[dict[str, Any]]:
    first_names = ["Aarav", "Maya", "Liam", "Sofia", "Noah", "Priya", "Ethan", "Zoe", "Mateo", "Nina"]
    last_names = ["Shah", "Chen", "Williams", "Patel", "Okafor", "Garcia"]
    roles = {
        "Engineering": [("Platform", "Backend Engineer", ["Python", "APIs", "AWS"]), ("Web", "Frontend Engineer", ["React", "TypeScript", "UX"]), ("Data", "Data Engineer", ["SQL", "Pipelines", "Analytics"]), ("Infrastructure", "DevOps Engineer", ["Kubernetes", "AWS", "Observability"])],
        "Product": [("Product", "Product Manager", ["Roadmaps", "Discovery", "Prioritization"]), ("Design", "Product Designer", ["Figma", "Research", "Prototyping"])],
        "Marketing": [("Growth", "Growth Marketer", ["Campaigns", "SEO", "Analytics"]), ("Brand", "Content Strategist", ["Content", "Brand", "Events"])],
        "Sales": [("Enterprise", "Account Executive", ["B2B", "Negotiation", "CRM"]), ("Success", "Customer Success Manager", ["Onboarding", "Renewals", "Discovery"])],
        "HR": [("People", "People Partner", ["Hiring", "Onboarding", "Culture"]), ("Talent", "Recruiter", ["Sourcing", "Interviews", "Employer Brand"])],
        "Finance": [("FP&A", "Financial Analyst", ["Budgets", "Forecasting", "Excel"]), ("Operations", "Finance Operations", ["Expenses", "Controls", "Vendors"])],
    }
    employees = []
    for index in range(60):
        department = DEPARTMENTS[index % len(DEPARTMENTS)]
        team, role, skills = roles[department][(index // len(DEPARTMENTS)) % len(roles[department])]
        name = f"{first_names[index % len(first_names)]} {last_names[index // len(first_names)]}"
        employees.append({"id": f"EMP-{index + 1:03d}", "name": name, "department": department, "team": team, "role": role, "skills": skills, "manager": "EMP-001" if index else None})
    return employees


def _projects(employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("PRJ-001", "Payments Reliability", "Engineering", "in progress", 58),
        ("PRJ-002", "Atlas Analytics", "Engineering", "at risk", 47),
        ("PRJ-003", "Customer Insights", "Product", "in progress", 42),
        ("PRJ-004", "Q3 Launch Campaign", "Marketing", "at risk", 36),
        ("PRJ-005", "Enterprise Expansion", "Sales", "in progress", 63),
        ("PRJ-006", "Nexora Onboarding", "HR", "in progress", 71),
        ("PRJ-007", "FY27 Planning", "Finance", "in progress", 52),
        ("PRJ-008", "Identity Refresh", "Engineering", "in progress", 76),
        ("PRJ-009", "Mobile Workspace", "Product", "in progress", 29),
        ("PRJ-010", "Partner Webinar", "Marketing", "complete", 100),
        ("PRJ-011", "Renewal Health", "Sales", "in progress", 68),
        ("PRJ-012", "People Operations", "HR", "in progress", 55),
    ]
    counters = {department: 0 for department in DEPARTMENTS}
    projects = []
    for index, (project_id, name, department, status, progress) in enumerate(specs):
        department_employees = [e for e in employees if e["department"] == department]
        owner = department_employees[counters[department] % len(department_employees)]
        counters[department] += 1
        members = [owner["id"]] + [e["id"] for e in department_employees[1:4]]
        projects.append({"id": project_id, "name": name, "department": department, "owner": owner["id"], "members": members, "status": status, "progress": progress, "start_date": (BASE_DATE - timedelta(days=26 - index)).date().isoformat(), "deadline": (BASE_DATE + timedelta(days=8 + index)).date().isoformat()})
    return projects


def _tasks(projects: list[dict[str, Any]], employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    templates = ["Define acceptance criteria", "Review implementation", "Validate stakeholder feedback", "Prepare launch checklist", "Resolve dependency", "Publish weekly update"]
    tasks = []
    for index in range(60):
        project = projects[index % len(projects)]
        owner = project["members"][index % len(project["members"])]
        status = "blocked" if index in {0, 1, 12, 18} else ("done" if index % 5 == 0 else "in progress")
        tasks.append({"id": f"TASK-{index + 1:03d}", "key": f"{project['id'].replace('PRJ', 'NX')}-{index + 101}", "title": f"{templates[index % len(templates)]} - {project['name']}", "project_id": project["id"], "assignee": owner, "status": status})
    return tasks


def _activity(timestamp: datetime, employee: dict[str, Any], project: dict[str, Any], activity_type: str, content: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"timestamp": timestamp.isoformat(), "employee": employee["id"], "department": employee["department"], "project": project["id"], "activity_type": activity_type, "content": content, "related_task": task["id"] if task else None}


def _source_id(prefix: str, number: int) -> str:
    return f"{prefix}-{number:04d}"


def _communications(employees: list[dict[str, Any]], projects: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {employee["id"]: employee for employee in employees}
    by_project = {project["id"]: project for project in projects}
    by_task = {task["id"]: task for task in tasks}

    def person(employee_id: str) -> dict[str, Any]:
        return by_id[employee_id]

    def project(project_id: str) -> dict[str, Any]:
        return by_project[project_id]

    def email(number: int, day: int, sender: str, recipients: list[str], subject: str, body: str, project_id: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        employee = person(sender)
        return {"id": _source_id("EMAIL", number), "sender": sender, "recipients": recipients, "timestamp": (BASE_DATE + timedelta(days=day, hours=10)).isoformat(), "subject": subject, "body": body, "department": employee["department"], "related_project": project_id, "related_task": task_id}

    def slack(number: int, day: int, channel: str, sender: str, message: str, project_id: str | None = None, task_id: str | None = None, thread_id: str | None = None, reply_to: str | None = None) -> dict[str, Any]:
        employee = person(sender)
        return {"id": _source_id("SLACK", number), "channel": channel, "sender": sender, "timestamp": (BASE_DATE + timedelta(days=day, hours=13 + number % 5, minutes=number % 12)).isoformat(), "message": message, "department": employee["department"], "related_project": project_id, "related_task": task_id, "thread_id": thread_id, "reply_to": reply_to}

    def meeting(number: int, day: int, title: str, participant_ids: list[str], department: str, project_id: str | None, transcript: str) -> dict[str, Any]:
        return {"meeting_id": _source_id("MEETING", number), "date": (BASE_DATE + timedelta(days=day)).date().isoformat(), "title": title, "participants": participant_ids, "department": department, "project": project_id, "transcript": transcript}

    engineering = [employee["id"] for employee in employees if employee["department"] == "Engineering"]
    product = [employee["id"] for employee in employees if employee["department"] == "Product"]
    marketing = [employee["id"] for employee in employees if employee["department"] == "Marketing"]
    hr = [employee["id"] for employee in employees if employee["department"] == "HR"]
    sales = [employee["id"] for employee in employees if employee["department"] == "Sales"]
    finance = [employee["id"] for employee in employees if employee["department"] == "Finance"]
    emails = [
        email(1, 2, engineering[0], [engineering[3]], "Payment webhook deployment is waiting on infrastructure", "The webhook retry code is ready, but I cannot deploy it until the production queue policy is approved.", "PRJ-001", "TASK-001"),
        email(2, 4, engineering[3], [engineering[0]], "Infrastructure dependency update", "The queue policy is still pending review. I expect to deploy the infrastructure change tomorrow afternoon.", "PRJ-001", "TASK-001"),
        email(3, 15, engineering[3], [engineering[0]], "Queue policy deployed", "The shared retry queue and alert routing are now deployed in staging. Please run webhook verification.", "PRJ-001", "TASK-013"),
        email(4, 18, engineering[0], [engineering[1], engineering[3]], "Webhook retry ready for review", "Verification passed after the infrastructure deployment. The pull request is ready for review.", "PRJ-001", "TASK-001"),
        email(5, 19, marketing[0], [marketing[1], product[0]], "Move Q3 campaign launch", "Can we move the campaign launch to Monday? The creative assets and customer proof points are not ready for Friday.", "PRJ-004", "TASK-016"),
        email(6, 23, marketing[1], [marketing[0]], "Campaign recovery plan", "I reduced the first launch scope and moved the missing creative review into the recovery plan.", "PRJ-004", "TASK-016"),
        email(7, 21, hr[0], [hr[1], engineering[0]], "Complete onboarding documents", "Please complete the onboarding documents before the new hire's first systems walkthrough.", "PRJ-006", "TASK-018"),
        email(8, 22, hr[1], [hr[0], engineering[0]], "New hire onboarding checklist", "Laptop, buddy assignment, and first-week meetings are confirmed. Access requests are being tracked.", "PRJ-006", "TASK-018"),
        email(9, 10, engineering[2], [engineering[0], product[0]], "Atlas event model decision", "I recommend that both analytics surfaces use the Atlas event model so we do not maintain two event-dimension implementations.", "PRJ-002", "TASK-014"),
        email(10, 12, product[0], [engineering[2], engineering[0]], "Roadmap decision: cohort exports", "The roadmap prioritizes Customer Insights cohort exports before mobile parity for the next release.", "PRJ-003", "TASK-015"),
        email(11, 26, engineering[0], [engineering[1]], "Payments runbook ownership", "The webhook decision has been discussed by only two engineers so far. Please document the runbook before rollout.", "PRJ-001", "TASK-001"),
        email(12, 24, finance[0], [sales[0], product[0]], "FY27 planning assumptions", "Please confirm the enterprise expansion forecast and product launch assumptions for the next planning review.", "PRJ-007", "TASK-007"),
    ]
    slack_messages = [
        slack(1, 3, "#eng-payments", engineering[0], "Webhook retry is implemented but I cannot deploy it yet.", "PRJ-001", "TASK-001", "THREAD-PAYMENTS-1"),
        slack(2, 3, "#eng-payments", engineering[3], "Infra deployment should be ready this afternoon if the queue policy review clears.", "PRJ-001", "TASK-001", "THREAD-PAYMENTS-1", "SLACK-0001"),
        slack(3, 3, "#eng-payments", engineering[0], "Okay, I will finish testing once it is deployed.", "PRJ-001", "TASK-001", "THREAD-PAYMENTS-1", "SLACK-0002"),
        slack(4, 5, "#eng-payments", engineering[1], "The dependency is still open. Should we use the shared retry queue rather than add another service?", "PRJ-001", "TASK-013", "THREAD-PAYMENTS-1"),
        slack(5, 10, "#eng-payments", engineering[0], "Decision recorded: shared retry queue plus standard alert thresholds.", "PRJ-001", "TASK-013", "THREAD-PAYMENTS-1"),
        slack(6, 16, "#eng-payments", engineering[3], "Queue policy is deployed in staging. Rahul can complete the webhook verification.", "PRJ-001", "TASK-013", "THREAD-PAYMENTS-1"),
        slack(7, 8, "#eng-analytics", engineering[2], "Atlas adds funnel cohorts and retention dimensions to the event model.", "PRJ-002", "TASK-014", "THREAD-ANALYTICS-1"),
        slack(8, 9, "#eng-analytics", engineering[5], "I am building a parallel event aggregation path for the dashboard. It overlaps with the Atlas dimensions.", "PRJ-002", "TASK-014", "THREAD-ANALYTICS-1", "SLACK-0007"),
        slack(9, 11, "#eng-analytics", engineering[0], "Let's stop duplicate work and consolidate on the Atlas event model.", "PRJ-002", "TASK-014", "THREAD-ANALYTICS-1"),
        slack(10, 20, "#marketing-launch", marketing[0], "Creative review is late, and the Q3 campaign launch is at risk.", "PRJ-004", "TASK-016", "THREAD-CAMPAIGN-1"),
        slack(11, 23, "#marketing-launch", marketing[1], "Recovery plan: launch the approved core assets Monday and move proof points to phase two.", "PRJ-004", "TASK-016", "THREAD-CAMPAIGN-1", "SLACK-0010"),
        slack(12, 22, "#people-ops", hr[0], "The new hire has a buddy and a first-week plan. Laptop delivery is confirmed.", "PRJ-006", "TASK-018", "THREAD-ONBOARDING-1"),
        slack(13, 21, "#sales-enterprise", sales[0], "The enterprise expansion opportunity needs updated security answers before the customer review.", "PRJ-005", "TASK-005", "THREAD-SALES-1"),
        slack(14, 24, "#finance-planning", finance[0], "Budget assumptions are ready for review. Waiting on the sales forecast and product launch dates.", "PRJ-007", "TASK-007", "THREAD-FINANCE-1"),
    ]
    meetings = [
        meeting(1, 6, "Payments dependency review", [engineering[0], engineering[1], engineering[3]], "Engineering", "PRJ-001", "Rahul said the webhook retry work is complete but cannot ship. Amit confirmed the queue policy is the dependency. The group agreed to use the shared retry queue and standard alert thresholds. Amit owns the infrastructure deployment; Rahul owns verification after deployment."),
        meeting(2, 11, "Analytics architecture sync", [engineering[0], engineering[2], engineering[5], product[0]], "Engineering", "PRJ-002", "The Atlas event model and the dashboard aggregation path contain overlapping funnel dimensions. The team agreed to consolidate on Atlas and retire the duplicate path. Maya will document the migration plan and Ethan will stop the parallel implementation."),
        meeting(3, 20, "Q3 campaign launch review", [marketing[0], marketing[1], product[0]], "Marketing", "PRJ-004", "Creative assets are incomplete and Friday is no longer realistic. The group moved the launch to Monday, reduced the first scope to approved assets, and assigned the proof-point review to Brand."),
        meeting(4, 22, "New hire first-week planning", [hr[0], hr[1], engineering[0]], "HR", "PRJ-006", "People Ops confirmed the laptop, buddy, and access requests. Engineering will host the systems walkthrough. The remaining action is to complete onboarding documents before the first day."),
        meeting(5, 25, "Payments rollout readiness", [engineering[0], engineering[1], engineering[3]], "Engineering", "PRJ-001", "The infrastructure issue is resolved and webhook verification passed in staging. Rahul and Maya are the only engineers who have led the technical decision discussion. The action is to publish a runbook so knowledge is not concentrated."),
        meeting(6, 27, "FY27 operating review", [finance[0], finance[1], sales[0], product[0]], "Finance", "PRJ-007", "Finance needs the latest sales forecast and product launch assumptions. Owners agreed to bring updated numbers to the next review."),
    ]
    return emails, slack_messages, meetings


def _activities(employees: list[dict[str, Any]], projects: list[dict[str, Any]], tasks: list[dict[str, Any]], days: int = 30) -> list[dict[str, Any]]:
    rng = random.Random(42)
    by_id = {e["id"]: e for e in employees}
    by_project = {p["id"]: p for p in projects}
    activities = []
    for day in range(days):
        for offset in range(10):
            project = projects[(day * 3 + offset) % len(projects)]
            employee = by_id[project["members"][offset % len(project["members"])] ]
            task = tasks[(day * 2 + offset) % len(tasks)]
            kind = ["GitHub commit", "Jira task update", "Slack message", "Meeting", "Email", "task completion", "GitHub pull request"][offset % 7]
            content = f"Progress update on {project['name']}: {task['title'].lower()}"
            activities.append(_activity(BASE_DATE + timedelta(days=day, hours=offset % 8, minutes=rng.randint(0, 45)), employee, project, kind, content, task))
    def add(day: int, employee_id: str, project_id: str, kind: str, content: str, task_id: str | None = None) -> None:
        activities.append(_activity(BASE_DATE + timedelta(days=day, hours=11), by_id[employee_id], by_project[project_id], kind, content, next((t for t in tasks if t["id"] == task_id), None)))
    eng = [e["id"] for e in employees if e["department"] == "Engineering"]
    add(3, eng[0], "PRJ-001", "Slack message", "Webhook retries are failing because the production queue policy is still pending.", "TASK-001")
    add(4, eng[3], "PRJ-001", "blocker", "Infrastructure dependency: queue policy and alert routing need approval.", "TASK-001")
    add(6, eng[1], "PRJ-001", "Meeting", "Payments dependency review: DevOps will ship the queue policy before the next deploy.", "TASK-001")
    add(10, eng[3], "PRJ-001", "decision", "Decision: use the shared retry queue and standard alert thresholds.", "TASK-002")
    add(15, eng[3], "PRJ-001", "task completion", "Queue policy deployed and verified in staging.", "TASK-002")
    add(17, eng[0], "PRJ-001", "GitHub pull request", "PR #183 implements webhook retries and is ready for review.", "TASK-001")
    add(19, eng[0], "PRJ-001", "task completion", "Webhook task completed after infrastructure dependency resolved.", "TASK-001")
    add(8, eng[2], "PRJ-002", "Jira task update", "Atlas event model adds funnel cohorts and retention dimensions.", "TASK-013")
    add(9, eng[5], "PRJ-002", "Slack message", "I am building a parallel event aggregation path for the analytics dashboard.", "TASK-019")
    add(11, eng[2], "PRJ-002", "Meeting", "Analytics overlap review: two teams are implementing the same event dimensions.", "TASK-013")
    add(12, eng[0], "PRJ-002", "decision", "Decision: consolidate on the Atlas event model; retire the duplicate dashboard path.", "TASK-019")
    product = [e["id"] for e in employees if e["department"] == "Product"]
    add(13, product[0], "PRJ-003", "decision", "Roadmap decision: Customer Insights ships cohort exports before mobile parity.", "TASK-025")
    marketing = [e["id"] for e in employees if e["department"] == "Marketing"]
    add(20, marketing[0], "PRJ-004", "blocker", "Launch campaign is behind schedule: creative review and customer proof points are late.", "TASK-019")
    add(23, marketing[1], "PRJ-004", "project update", "Campaign recovery plan approved with a smaller launch scope.", "TASK-020")
    hr = [e["id"] for e in employees if e["department"] == "HR"]
    add(22, hr[0], "PRJ-006", "Email", "New hire onboarding is underway; laptop, buddy, and first-week plan are ready.", "TASK-031")
    add(25, eng[0], "PRJ-001", "decision", "Payments technical decision is currently concentrated with two engineers; document the runbook.", "TASK-001")
    return sorted(activities, key=lambda item: item["timestamp"])


def generate_demo_data(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    employees = _employee_catalog()
    projects = _projects(employees)
    tasks = _tasks(projects, employees)
    emails, slack_messages, meetings = _communications(employees, projects, tasks)
    activities = _activities(employees, projects, tasks)
    company = {"name": "Nexora Technologies", "generated_at": datetime.now(timezone.utc).isoformat(), "departments": DEPARTMENTS, "days": 30, "source_counts": {"gmail": len(emails), "slack": len(slack_messages), "meetings": len(meetings), "legacy_activity": len(activities)}}
    records = {"company": company, "employees": employees, "projects": projects, "tasks": tasks, "activities": activities, "gmail": emails, "slack": slack_messages, "meetings": meetings}
    for name, value in records.items():
        (output / f"{name}.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
    build_database(records, output.parent / "nexora.db")
    return records
