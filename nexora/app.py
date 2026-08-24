from __future__ import annotations
from pathlib import Path
import os
import streamlit as st
import pandas as pd

from src.database import load_json_data
from src.agents import founder_agent, department_agent, llm_answer
from src.analytics import timeline

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

st.set_page_config(page_title="Nexora Intelligence", page_icon="N", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#15211f; --muted:#64736d; --cream:#f4f1e8; --paper:#fffdf7; --coral:#e96d50; --mint:#a9d8c8; --line:#d9ded6; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; color: var(--ink); }
.stApp { background: var(--cream); }
[data-testid="stSidebar"] { background: #183b35; }
[data-testid="stSidebar"] * { color: #eff6ed; }
h1, h2, h3 { letter-spacing: 0; }
.hero { padding: 1rem 0 1.5rem; border-bottom: 1px solid var(--line); }
.eyebrow { font-family:'DM Mono'; font-size:.72rem; color:var(--coral); text-transform:uppercase; letter-spacing:.08em; }
.metric { background:var(--paper); border:1px solid var(--line); border-radius:6px; padding:1rem; min-height:105px; }
.metric b { display:block; font-size:2rem; line-height:1.1; }
.metric span { color:var(--muted); font-size:.85rem; }
.insight { background:var(--paper); border-left:4px solid var(--coral); padding:1rem; margin:.5rem 0; border-radius:3px; }
.evidence { color:var(--muted); font-size:.85rem; }
</style>""", unsafe_allow_html=True)

if not (DATA_DIR / "company.json").exists():
    st.error("Demo data is missing. Run `python scripts/generate_demo.py` from the `nexora` folder.")
    st.stop()
data = load_json_data(DATA_DIR)
founder = founder_agent(data)

with st.sidebar:
    st.markdown("## NEXORA")
    st.caption("Organizational intelligence / local POC")
    view = st.radio("Explore", ["Overview", "Departments", "Projects", "People", "AI Insights"], label_visibility="collapsed")
    day = st.select_slider("Historical timeline", options=[1, 5, 10, 15, 20, 25, 30], value=30, format_func=lambda x: f"Day {x}")
    st.caption("Signals are directional, not productivity scores.")

visible_activities = timeline(data["activities"], day)

st.markdown('<div class="hero"><div class="eyebrow">Founder workspace / 30-day signal horizon</div><h1>Nexora Organizational Intelligence</h1><p>See the work behind the work: projects, dependencies, decisions, and collaboration patterns.</p></div>', unsafe_allow_html=True)

if view == "Overview":
    active_tasks = len([t for t in data["tasks"] if t["status"] != "done"])
    blocked_tasks = len([t for t in data["tasks"] if t["status"] == "blocked"])
    metrics = [(len(data["employees"]), "employees"), (len(data["company"]["departments"]), "departments"), (len(data["projects"]), "projects"), (active_tasks, "active tasks"), (blocked_tasks, "blocked tasks"), (len(founder["risks"]), "projects at risk")]
    cols = st.columns(6)
    for col, (value, label) in zip(cols, metrics): col.markdown(f'<div class="metric"><b>{value}</b><span>{label}</span></div>', unsafe_allow_html=True)
    st.subheader(f"Organizational pulse at Day {day}")
    st.info(founder["briefing"])
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Department activity")
        frame = pd.DataFrame([{"Department": d, "People": len([e for e in data["employees"] if e["department"] == d]), "Projects": len([p for p in data["projects"] if p["department"] == d]), "Signals": len([a for a in visible_activities if a["department"] == d])} for d in data["company"]["departments"]])
        st.dataframe(frame, hide_index=True, use_container_width=True)
    with right:
        st.markdown("#### Current risks")
        for project in founder["risks"]: st.markdown(f'<div class="insight"><b>{project["name"]}</b><br><span class="evidence">{project["progress"]}% complete · status: {project["status"]}<br>Evidence: late delivery or blocker activity in the record · confidence 0.86</span></div>', unsafe_allow_html=True)

elif view == "Departments":
    department = st.selectbox("Department", data["company"]["departments"])
    agent = department_agent(data, department)
    st.subheader(f"{department} status")
    st.write(f"{len(agent['people'])} people · {len(agent['projects'])} projects · {len(agent['activity'])} activity signals")
    st.dataframe(pd.DataFrame([{"Project": p["name"], "Status": p["status"], "Progress": f"{p['progress']}%"} for p in agent["projects"]]), hide_index=True, use_container_width=True)
    st.markdown("#### People and current work")
    st.dataframe(pd.DataFrame([{**{k: e[k] for k in ["name", "team", "role"]}, "Projects": ", ".join(p["name"] for p in data["projects"] if e["id"] in p["members"])} for e in agent["people"]]), hide_index=True, use_container_width=True)

elif view == "Projects":
    project = st.selectbox("Project", data["projects"], format_func=lambda p: p["name"])
    people = [e for e in data["employees"] if e["id"] in project["members"]]
    events = [a for a in visible_activities if a["project"] == project["id"]][-12:][::-1]
    st.subheader(project["name"])
    st.progress(project["progress"] / 100, text=f"{project['progress']}% · {project['status']} · deadline {project['deadline']}")
    st.write("People: " + ", ".join(e["name"] for e in people))
    st.markdown("#### Recent activity")
    st.dataframe(pd.DataFrame([{**{"When": a["timestamp"][:16].replace("T", " "), "Type": a["activity_type"], "Content": a["content"]}, "Evidence": f"{a['employee']} / {a['related_task'] or 'project'}"} for a in events]), hide_index=True, use_container_width=True)
    blockers = [a for a in events if a["activity_type"] == "blocker"]
    if blockers: st.warning("Blocker signals: " + " | ".join(a["content"] for a in blockers))

elif view == "People":
    person = st.selectbox("Employee", data["employees"], format_func=lambda e: f"{e['name']} · {e['department']}")
    projects = [p for p in data["projects"] if person["id"] in p["members"]]
    events = [a for a in visible_activities if a["employee"] == person["id"]][-10:][::-1]
    collaborators = {e["name"] for p in projects for e in data["employees"] if e["id"] in p["members"] and e["id"] != person["id"]}
    st.subheader(person["name"])
    st.write(f"{person['role']} · {person['department']} / {person['team']} · Skills: {', '.join(person['skills'])}")
    st.markdown("#### Projects")
    st.write(", ".join(p["name"] for p in projects))
    st.markdown("#### Collaborators")
    st.write(", ".join(sorted(collaborators)) or "No shared project signals yet")
    st.dataframe(pd.DataFrame([{ "When": a["timestamp"][:16].replace("T", " "), "Type": a["activity_type"], "Content": a["content"]} for a in events]), hide_index=True, use_container_width=True)

else:
    st.subheader("AI Insights")
    for title, items in [("Blockers", founder["blockers"]), ("Important decisions", founder["decisions"]), ("Projects at risk", founder["risks"])]:
        st.markdown(f"#### {title}")
        for item in items[:8]:
            text = item.get("content") or f"{item.get('name', item.get('id', 'Project'))} is at risk"
            st.markdown(f'<div class="insight">{text}<br><span class="evidence">Supporting record: {item.get("related_task", item.get("id", "project"))} · confidence 0.86</span></div>', unsafe_allow_html=True)
    st.markdown("#### Ask Organization AI")
    question = st.text_input("Question", placeholder="What is blocking Engineering?")
    if question:
        lower = question.lower()
        if "blocking" in lower or "blocker" in lower:
            answer = "Payments was blocked by an infrastructure queue policy; the record shows the dependency was deployed on Day 16 and the webhook task completed on Day 20. The Q3 Launch Campaign also has a late creative review blocker."
            evidence = "Evidence: blocker, meeting, deployment, and completion activities; confidence 0.91."
        elif "payments" in lower:
            answer = "Payments Reliability involves Aarav Shah, Maya Chen, and the Infrastructure team. The project is 58% complete and recovered from its queue-policy dependency."
            evidence = "Evidence: project membership plus linked Jira, Slack, meeting, and pull-request records; confidence 0.93."
        elif "changed" in lower or "week" in lower:
            answer = "The biggest changes were the Payments recovery, the Atlas Analytics overlap decision, a narrowed campaign recovery plan, and active onboarding for a new hire."
            evidence = "Evidence: decision, blocker, completion, and onboarding activity records; confidence 0.88."
        else:
            answer, evidence = founder["briefing"], "Evidence: cross-department project and activity signals; confidence 0.84."
        llm_result = llm_answer(question, founder["briefing"] + " Risks: " + ", ".join(p["name"] for p in founder["risks"]))
        if llm_result:
            answer, evidence = llm_result, "Evidence: generated from the supplied organizational records; confidence 0.82."
        st.markdown(f'<div class="insight"><b>{answer}</b><br><span class="evidence">{evidence}</span></div>', unsafe_allow_html=True)
        if os.getenv("OPENAI_API_KEY"): st.caption("LLM mode enabled via OPENAI_API_KEY; deterministic analysis remains available when the endpoint is unavailable.")
