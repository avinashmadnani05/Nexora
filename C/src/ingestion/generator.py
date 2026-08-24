"""Generate Nexora Technologies synthetic organization and communication."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.config import GENERATED_DIR

random.seed(42)

DEPARTMENTS = ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance"]

FIRST_NAMES = [
    "Rahul", "Amit", "Priya", "Sneha", "Vikram", "Ananya", "Karan", "Meera",
    "Arjun", "Divya", "Rohan", "Neha", "Sanjay", "Kavita", "Deepak", "Pooja",
    "Nikhil", "Shreya", "Aditya", "Ritu", "Manish", "Swati", "Gaurav", "Tanvi",
    "Rajesh", "Isha", "Varun", "Anjali", "Suresh", "Preeti", "Harish", "Nidhi",
    "Ashok", "Komal", "Ravi", "Sunita", "Mohit", "Rekha", "Vinod", "Lakshmi",
    "Pradeep", "Geeta", "Sunil", "Madhuri", "Anil", "Sarita", "Dinesh", "Uma",
    "Ramesh", "Padma", "Krishna", "Radha", "Balaji", "Latha", "Srinivas", "Vijaya",
    "Chandra", "Indira", "Murali", "Kamala",
]

LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Reddy", "Nair", "Iyer",
    "Menon", "Joshi", "Desai", "Rao", "Verma", "Malhotra", "Kapoor", "Chopra",
    "Banerjee", "Mukherjee", "Das", "Pillai", "Shetty", "Kulkarni", "Mehta",
    "Shah", "Agarwal", "Bose", "Chatterjee", "Dutta", "Ghosh", "Sinha",
]

PROJECTS = [
    {"id": "PRJ-001", "name": "Payments Platform", "department": "Engineering", "status": "in_progress"},
    {"id": "PRJ-002", "name": "Mobile App v2", "department": "Product", "status": "in_progress"},
    {"id": "PRJ-003", "name": "Q3 Brand Campaign", "department": "Marketing", "status": "in_progress"},
    {"id": "PRJ-004", "name": "Enterprise Sales Pipeline", "department": "Sales", "status": "in_progress"},
    {"id": "PRJ-005", "name": "Analytics Dashboard", "department": "Engineering", "status": "in_progress"},
    {"id": "PRJ-006", "name": "Customer Analytics Portal", "department": "Product", "status": "in_progress"},
    {"id": "PRJ-007", "name": "HR Onboarding System", "department": "HR", "status": "in_progress"},
    {"id": "PRJ-008", "name": "Budget Planning FY26", "department": "Finance", "status": "in_progress"},
    {"id": "PRJ-009", "name": "API Gateway Upgrade", "department": "Engineering", "status": "in_progress"},
    {"id": "PRJ-010", "name": "Partner Integration Hub", "department": "Sales", "status": "in_progress"},
    {"id": "PRJ-011", "name": "Security Compliance Audit", "department": "Engineering", "status": "in_progress"},
    {"id": "PRJ-012", "name": "Content Management Revamp", "department": "Marketing", "status": "in_progress"},
]

TEAMS = {
    "Engineering": ["Platform", "Payments", "Infrastructure", "Mobile", "Data"],
    "Product": ["Core Product", "Growth", "Enterprise"],
    "Marketing": ["Brand", "Growth Marketing", "Content"],
    "Sales": ["Enterprise", "SMB", "Partnerships"],
    "HR": ["Talent", "People Ops"],
    "Finance": ["FP&A", "Accounting"],
}

ROLES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Staff Engineer", "Engineering Manager", "DevOps Engineer"],
    "Product": ["Product Manager", "Senior PM", "Product Analyst", "Director of Product"],
    "Marketing": ["Marketing Manager", "Content Strategist", "Campaign Manager", "Designer"],
    "Sales": ["Account Executive", "Sales Manager", "SDR", "Sales Director"],
    "HR": ["HR Manager", "Recruiter", "People Partner"],
    "Finance": ["Financial Analyst", "Controller", "Finance Manager"],
}


def _name(i: int) -> str:
    return f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[i % len(LAST_NAMES)]}"


def generate_employees(n: int = 60) -> list[dict]:
    employees = []
    dept_counts = {d: 0 for d in DEPARTMENTS}
    per_dept = n // len(DEPARTMENTS)
    idx = 0
    managers = {}

    for dept in DEPARTMENTS:
        mgr_id = f"EMP-{idx+1:03d}"
        managers[dept] = mgr_id
        employees.append({
            "id": mgr_id,
            "name": _name(idx),
            "department": dept,
            "team": TEAMS[dept][0],
            "role": f"{dept} Manager" if dept != "Engineering" else "Engineering Manager",
            "manager": None,
            "skills": ["leadership", "strategy"],
        })
        idx += 1

    for dept in DEPARTMENTS:
        remaining = per_dept - 1
        for j in range(remaining):
            team = TEAMS[dept][j % len(TEAMS[dept])]
            role = ROLES[dept][j % len(ROLES[dept])]
            employees.append({
                "id": f"EMP-{idx+1:03d}",
                "name": _name(idx),
                "department": dept,
                "team": team,
                "role": role,
                "manager": managers[dept],
                "skills": random.sample(["python", "react", "sql", "communication", "analytics", "sales", "design"], 3),
            })
            idx += 1

    return employees[:n]


def generate_projects(employees: list[dict]) -> list[dict]:
    start = datetime(2026, 7, 1)
    projects = []
    for p in PROJECTS:
        dept_emps = [e for e in employees if e["department"] == p["department"]]
        owner = dept_emps[0]["id"] if dept_emps else employees[0]["id"]
        members = [e["id"] for e in dept_emps[:5]]
        projects.append({
            **p,
            "owner": owner,
            "members": members,
            "progress": random.randint(30, 70),
            "start_date": start.strftime("%Y-%m-%d"),
            "deadline": (start + timedelta(days=60)).strftime("%Y-%m-%d"),
        })
    return projects


def generate_tasks(projects: list[dict], employees: list[dict]) -> list[dict]:
    tasks = []
    tid = 1
    for p in projects:
        for i in range(random.randint(4, 10)):
            dept_emps = [e for e in employees if e["department"] == p["department"]]
            assignee = random.choice(dept_emps)["id"] if dept_emps else employees[0]["id"]
            tasks.append({
                "id": f"TSK-{tid:03d}",
                "name": f"{p['name']} task {i+1}",
                "project_id": p["id"],
                "assignee": assignee,
                "status": random.choice(["open", "in_progress", "done", "blocked"]),
                "priority": random.choice(["low", "medium", "high"]),
                "created_at": "2026-07-01",
                "updated_at": "2026-08-15",
            })
            tid += 1
    return tasks


def _emp_by_name(employees, name_part):
    for e in employees:
        if name_part.lower() in e["name"].lower():
            return e
    return employees[0]


def generate_communications(employees: list[dict], projects: list[dict], days: int = 30) -> dict:
    """Generate semantically connected 30-day communication across all demo scenarios."""
    base_date = datetime(2026, 7, 22)
    gmail, slack, meetings, jira = [], [], [], []
    msg_id = 1

    rahul = _emp_by_name(employees, "Rahul")
    amit = _emp_by_name(employees, "Amit")
    priya = _emp_by_name(employees, "Priya")
    sneha = _emp_by_name(employees, "Sneha")
    vikram = _emp_by_name(employees, "Vikram")
    ananya = _emp_by_name(employees, "Ananya")

    payments = next(p for p in projects if p["name"] == "Payments Platform")
    campaign = next(p for p in projects if p["name"] == "Q3 Brand Campaign")
    analytics_eng = next(p for p in projects if p["name"] == "Analytics Dashboard")
    analytics_prod = next(p for p in projects if p["name"] == "Customer Analytics Portal")

    def ts(day_offset, hour, minute=0):
        return (base_date + timedelta(days=day_offset, hours=hour, minutes=minute)).isoformat()

    def add_slack(day, hour, sender, channel, message, dept, project_id, thread=None):
        nonlocal msg_id
        slack.append({
            "id": f"SLK-{msg_id:04d}", "channel": channel, "sender": sender["id"],
            "timestamp": ts(day, hour), "message": message,
            "department": dept, "project_id": project_id, "thread_id": thread,
        })
        mid = f"SLK-{msg_id:04d}"
        msg_id += 1
        return mid

    def add_gmail(day, hour, sender, recipients, subject, body, dept, project_id):
        nonlocal msg_id
        gmail.append({
            "id": f"EML-{msg_id:04d}", "sender": sender["id"],
            "recipients": [r["id"] for r in recipients], "timestamp": ts(day, hour),
            "subject": subject, "body": body, "department": dept, "project_id": project_id,
        })
        mid = f"EML-{msg_id:04d}"
        msg_id += 1
        return mid

    def add_meeting(day, hour, participants, dept, project_id, transcript):
        nonlocal msg_id
        meetings.append({
            "id": f"MTG-{msg_id:04d}", "date": ts(day, hour),
            "participants": [p["id"] for p in participants],
            "department": dept, "project_id": project_id, "transcript": transcript,
        })
        mid = f"MTG-{msg_id:04d}"
        msg_id += 1
        return mid

    def add_jira(day, hour, task_id, assignee, comment, dept, project_id, status):
        nonlocal msg_id
        jira.append({
            "id": f"JIR-{msg_id:04d}", "task_id": task_id, "assignee": assignee["id"],
            "timestamp": ts(day, hour), "comment": comment, "department": dept,
            "project_id": project_id, "status": status, "summary": comment[:80],
        })
        msg_id += 1

    # --- Scenario 1: Payments infrastructure blocker ---
    add_slack(0, 10, rahul, "engineering-payments", 
              "Starting work on the webhook retry logic for Payments. Should be straightforward.", 
              "Engineering", payments["id"])
    add_slack(2, 14, rahul, "engineering-payments",
              "I've finished the retry logic but deployment is still blocked. Can't push to staging without infra.",
              "Engineering", payments["id"])
    add_gmail(2, 15, rahul, [amit], "Payments webhook - staging deployment needed",
              "Hi Amit, I need the staging queue configured for Payments webhook testing. "
              "Can someone from infra confirm whether the staging queue is ready?",
              "Engineering", payments["id"])
    add_gmail(3, 9, amit, [rahul], "Re: Payments webhook - staging deployment needed",
              "Rahul, infrastructure deployment for the staging queue is still pending. "
              "We're waiting on the security review before we can deploy. Should be done by end of week.",
              "Engineering", payments["id"])
    add_meeting(4, 11, [rahul, amit, vikram], "Engineering", payments["id"],
                "Engineering standup. Rahul: Payments webhook is blocked on infrastructure deployment. "
                "Amit: Security review is the gating item. Vikram: This puts the launch timeline at risk.")
    add_jira(4, 14, "PAY-183", rahul, "Blocked: waiting for infrastructure to deploy webhook changes", 
             "Engineering", payments["id"], "blocked")
    add_slack(8, 10, amit, "engineering-infra",
              "Staging queue deployment is complete. Rahul, you should be unblocked now.",
              "Engineering", payments["id"])
    add_jira(10, 16, "PAY-183", rahul, "Infrastructure dependency resolved. Resuming webhook work.",
             "Engineering", payments["id"], "in_progress")
    add_slack(12, 17, rahul, "engineering-payments",
              "Webhook retry logic deployed and tested. PR merged. Payments webhook reliability is done.",
              "Engineering", payments["id"])
    add_jira(12, 18, "PAY-183", rahul, "Completed: webhook retry logic merged to main.",
             "Engineering", payments["id"], "done")

    # --- Scenario 2: Marketing campaign delay ---
    add_slack(1, 11, priya, "marketing-campaigns",
              "Q3 brand campaign creative assets are behind schedule. Design team hasn't delivered the hero banners.",
              "Marketing", campaign["id"])
    add_gmail(3, 10, priya, [sneha], "Q3 Campaign - creative delay",
              "Sneha, we need to discuss pushing the campaign launch. Creative assets for the hero section "
              "and social templates are still incomplete. Can we move launch to Monday next week?",
              "Marketing", campaign["id"])
    add_slack(5, 14, sneha, "marketing-campaigns",
              "Let's push the campaign launch to Monday. Design is still working on the hero banners.",
              "Marketing", campaign["id"])
    add_meeting(6, 10, [priya, sneha, ananya], "Marketing", campaign["id"],
                "Campaign planning meeting. Decision: launch moved from Thursday to Monday due to incomplete "
                "creative assets. Ananya to prioritize hero banner delivery by Friday.")

    # --- Scenario 3: Duplicate analytics work ---
    add_slack(3, 11, vikram, "engineering-data",
              "Starting scoping for the analytics dashboard — real-time metrics, user funnels, retention charts.",
              "Engineering", analytics_eng["id"])
    add_slack(4, 15, ananya, "product-growth",
              "Product team is planning a customer analytics portal with funnel analysis and retention views. "
              "Overlapping with what engineering might be building?",
              "Product", analytics_prod["id"])
    add_slack(5, 10, vikram, "engineering-data",
              "Didn't realize Product was also building analytics dashboards. We should sync to avoid duplicate work.",
              "Engineering", analytics_eng["id"])
    add_meeting(7, 14, [vikram, ananya, _emp_by_name(employees, "Karan")], "Product", analytics_prod["id"],
                "Cross-team sync on analytics. Identified overlap between Engineering's Analytics Dashboard "
                "and Product's Customer Analytics Portal. Agreed to consolidate requirements.")

    # --- Scenario 4: Technical decision (async processing) ---
    add_slack(6, 11, rahul, "engineering-platform",
              "Proposal: use asynchronous processing for the Payments notification workflow instead of sync calls.",
              "Engineering", payments["id"])
    add_gmail(7, 9, rahul, [vikram, _emp_by_name(employees, "Karan")], 
              "Decision needed: async processing for Payments notifications",
              "We agreed to use asynchronous processing for the Payments notification workflow. "
              "This will improve reliability and decouple the webhook handler from downstream services.",
              "Engineering", payments["id"])
    add_meeting(8, 15, [rahul, vikram, _emp_by_name(employees, "Karan")], "Engineering", payments["id"],
                "Architecture review. Decision confirmed: Payments notifications will use async message queue "
                "processing. Rahul to implement. Target: next sprint.")

    # --- Scenario 5: HR onboarding ---
    new_hire = employees[-1]
    hr_mgr = _emp_by_name(employees, "Deepak") if any("Deepak" in e["name"] for e in employees) else employees[50]
    add_gmail(9, 9, hr_mgr, [new_hire], f"Welcome to Nexora — onboarding checklist",
              f"Welcome aboard! I'll take ownership of the onboarding checklist for you. "
              f"Day 1: HR orientation at 10am. Day 2: Engineering team intro. Please complete the compliance training.",
              "HR", projects[6]["id"])
    add_meeting(10, 10, [hr_mgr, new_hire, rahul], "HR", projects[6]["id"],
                f"Onboarding session for {new_hire['name']}. Covered company policies, tools access, and team introductions. "
                f"New hire assigned to Platform team under Engineering.")

    # --- Scenario 6: Project recovery (API Gateway) ---
    api_gw = next(p for p in projects if p["name"] == "API Gateway Upgrade")
    add_slack(11, 9, amit, "engineering-infra",
              "API Gateway upgrade is at risk — performance tests failing on the new routing layer.",
              "Engineering", api_gw["id"])
    add_jira(13, 11, "API-042", amit, "Project at risk: performance test failures on routing layer",
             "Engineering", api_gw["id"], "blocked")
    add_slack(15, 14, amit, "engineering-infra",
              "Found the routing bottleneck — connection pool misconfiguration. Fix deployed.",
              "Engineering", api_gw["id"])
    add_jira(17, 16, "API-042", amit, "Performance tests passing. Project back on track.",
             "Engineering", api_gw["id"], "done")

    # --- Scenario 7: Knowledge concentration ---
    add_slack(2, 16, rahul, "engineering-payments", "Only I have access to the legacy payment processor config.", 
              "Engineering", payments["id"])
    add_slack(9, 11, rahul, "engineering-payments", 
              "Another question about the payment processor — I'm the only one who knows this system.",
              "Engineering", payments["id"])
    add_slack(14, 10, vikram, "engineering-platform",
              "We need to document the payment processor setup. Rahul is a single point of failure here.",
              "Engineering", payments["id"])

    # --- General background communications ---
    for day in range(days):
        for _ in range(random.randint(2, 5)):
            emp = random.choice(employees)
            proj = random.choice([p for p in projects if p["department"] == emp["department"]] or projects)
            messages = [
                f"Quick update on {proj['name']} — making progress on my assigned items.",
                f"Can we sync on {proj['name']} priorities for this week?",
                f"Completed the review for {proj['name']}. Ready for next steps.",
                f"Flagging a dependency on another team for {proj['name']}.",
                f"Product wants the {proj['name']} feature before the September release.",
            ]
            add_slack(day, random.randint(9, 17), emp, f"{emp['department'].lower()}-general",
                      random.choice(messages), emp["department"], proj["id"])

    return {"gmail": gmail, "slack": slack, "meetings": meetings, "jira": jira}


def generate_all(output_dir: Path = None) -> dict:
    output_dir = output_dir or GENERATED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    employees = generate_employees(60)
    departments = [{"id": f"DEPT-{i+1}", "name": d} for i, d in enumerate(DEPARTMENTS)]
    teams = []
    for dept, team_list in TEAMS.items():
        for j, t in enumerate(team_list):
            teams.append({"id": f"TEAM-{dept[:3].upper()}-{j+1}", "name": t, "department": dept})

    projects = generate_projects(employees)
    tasks = generate_tasks(projects, employees)
    comms = generate_communications(employees, projects)

    data = {
        "company": {"name": "Nexora Technologies", "employees_count": len(employees)},
        "employees": employees,
        "departments": departments,
        "teams": teams,
        "projects": projects,
        "tasks": tasks,
        **comms,
    }

    for key in ["employees", "departments", "teams", "projects", "tasks", "gmail", "slack", "meetings", "jira"]:
        with open(output_dir / f"{key}.json", "w") as f:
            json.dump(data[key], f, indent=2)

    with open(output_dir / "organization.json", "w") as f:
        json.dump(data, f, indent=2)

    return data
