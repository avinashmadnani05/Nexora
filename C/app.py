"""Nexora Organizational Intelligence Platform — Streamlit Demo."""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.agents.base_agent import get_agent
from src.agents.briefing import generate_daily_brief
from src.analytics.insights import (
    get_ai_insights,
    get_department_insights,
    get_org_overview,
    get_work_involvement_signals,
)
from src.intelligence.memory import OrganizationalMemory
from src.models.database import init_db, query
from src.utils.config import get_config

st.set_page_config(page_title="Nexora Intelligence", page_icon="🏢", layout="wide")

init_db()
memory = OrganizationalMemory()
cfg = get_config()

st.sidebar.title("Nexora Intelligence")
page = st.sidebar.radio(
    "Navigate",
    [
        "Organization Overview",
        "Department Intelligence",
        "Projects",
        "People",
        "Communication Timeline",
        "AI Insights",
        "Chat",
        "Daily Brief",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(f"LLM: **{cfg['llm_provider']}** | DB: SQLite")


def _has_data() -> bool:
    return len(query("SELECT id FROM employees LIMIT 1")) > 0


if not _has_data():
    st.warning("No data loaded. Run setup first:")
    st.code("python scripts/setup_demo.py", language="bash")
    if st.button("Run Setup Now"):
        with st.spinner("Generating and processing demo data..."):
            from scripts.setup_demo import main
            main()
        st.success("Demo data loaded!")
        st.rerun()


# --- Organization Overview ---
if page == "Organization Overview":
    st.title("Organization Overview")
    overview = get_org_overview()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Employees", overview["employee_count"])
    c2.metric("Departments", overview["department_count"])
    c3.metric("Projects", overview["project_count"])
    c4.metric("Active Tasks", overview["active_tasks"])
    c5.metric("Blocked Tasks", overview["blocked_tasks"])

    st.subheader("Projects at Risk")
    if overview["projects_at_risk"]:
        st.dataframe(pd.DataFrame(overview["projects_at_risk"]), use_container_width=True)
    else:
        st.info("No projects currently flagged at risk.")

    st.subheader("Active Blockers")
    blockers = memory.get_blockers()
    if blockers:
        st.dataframe(pd.DataFrame(blockers)[["summary", "dependency", "status", "timestamp"]], use_container_width=True)
    else:
        st.info("No active blockers.")


# --- Department Intelligence ---
elif page == "Department Intelligence":
    st.title("Department Intelligence")
    dept = st.selectbox("Department", ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance"])
    insights = get_department_insights(dept)
    c1, c2, c3 = st.columns(3)
    c1.metric("Projects", insights["projects"])
    c2.metric("Events", insights["events"])
    c3.metric("Blockers", insights["blockers"])
    if insights["event_breakdown"]:
        st.bar_chart(pd.Series(insights["event_breakdown"]))
    if insights["recent_events"]:
        st.subheader("Recent Events")
        for e in insights["recent_events"]:
            st.markdown(f"**{e.get('event_type', 'update')}** — {e.get('summary', '')[:120]}")


# --- Projects ---
elif page == "Projects":
    st.title("Projects")
    projects = memory.get_projects()
    selected = st.selectbox("Select Project", projects, format_func=lambda p: p["name"])
    if selected:
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", selected.get("status", "unknown"))
        c2.metric("Progress", f"{selected.get('progress', 0)}%")
        c3.metric("Deadline", selected.get("deadline", "N/A"))

        comms = memory.get_communications_for_project(selected["id"])
        events = memory.get_events(project_id=selected["id"])
        blockers = [b for b in memory.get_blockers(active_only=False) if b.get("project_id") == selected["id"]]

        tab1, tab2, tab3 = st.tabs(["Communications", "Events", "Blockers"])
        with tab1:
            for c in comms[-10:]:
                st.markdown(f"**{c.get('source', '').upper()}** `{c.get('timestamp', '')[:16]}` — {c.get('content', '')[:200]}")
        with tab2:
            for e in events[-15:]:
                st.markdown(f"**{e.get('event_type')}** ({e.get('timestamp', '')[:16]}): {e.get('summary', '')[:150]}")
        with tab3:
            if blockers:
                st.dataframe(pd.DataFrame(blockers), use_container_width=True)
            else:
                st.info("No blockers for this project.")


# --- People ---
elif page == "People":
    st.title("People")
    employees = memory.get_employees()
    selected = st.selectbox("Select Employee", employees, format_func=lambda e: f"{e['name']} — {e['role']}")
    if selected:
        st.markdown(f"**Department:** {selected['department']} | **Team:** {selected.get('team', 'N/A')}")
        signals = get_work_involvement_signals(selected["id"])
        c1, c2 = st.columns(2)
        c1.metric("Communications", signals["communication_count"])
        c2.metric("Organizational Events", signals["event_count"])
        st.subheader("Work Involvement Signals")
        if signals["recent_events"]:
            for e in signals["recent_events"]:
                st.markdown(f"• {e.get('summary', '')[:100]}")
        else:
            st.info("No recent work signals detected.")


# --- Communication Timeline ---
elif page == "Communication Timeline":
    st.title("Communication Timeline")
    st.caption("How raw communication becomes organizational events")
    proj_list = memory.get_projects()
    pay_proj = next((p for p in proj_list if "Payment" in p["name"]), proj_list[0] if proj_list else None)
    if pay_proj:
        comms = memory.get_communications_for_project(pay_proj["id"])
        events = memory.get_events(project_id=pay_proj["id"])
        timeline = []
        for c in comms:
            timeline.append({"time": c.get("timestamp", ""), "type": c.get("source", "").upper(), "text": c.get("content", "")[:100], "kind": "comm"})
        for e in events:
            if e.get("event_type") in ("blocker", "resolution", "decision"):
                timeline.append({"time": e.get("timestamp", ""), "type": e.get("event_type", "").upper(), "text": e.get("summary", "")[:100], "kind": "event"})
        timeline.sort(key=lambda x: x["time"])
        for item in timeline[:20]:
            icon = "📨" if item["kind"] == "comm" else "⚡"
            st.markdown(f"{icon} **{item['time'][:16]}** [{item['type']}] ↓")
            st.markdown(f"   {item['text']}")
            st.markdown("")


# --- AI Insights ---
elif page == "AI Insights":
    st.title("AI Insights")
    insights = get_ai_insights()
    tab1, tab2, tab3, tab4 = st.tabs(["Blockers & Risks", "Decisions", "Duplicate Work", "Knowledge Concentration"])
    with tab1:
        if insights["risks"]:
            for r in insights["risks"]:
                st.warning(r.get("summary", "")[:200])
        else:
            st.info("No risks detected.")
    with tab2:
        for d in insights["decisions"]:
            st.success(d.get("summary", "")[:200])
    with tab3:
        for d in insights["duplicate_work"]:
            st.info(d.get("summary", "")[:200])
        if not insights["duplicate_work"]:
            st.info("No duplicate work signals.")
    with tab4:
        for k in insights["knowledge_concentration"]:
            st.markdown(f"**{k['person']}** — {k['mentions']} organizational mentions")
        for kr in insights["knowledge_risks"]:
            st.error(kr.get("summary", "")[:200])


# --- Chat ---
elif page == "Chat":
    st.title("Organizational Intelligence Chat")
    role = st.selectbox("Agent Role", ["Founder", "Engineering", "Marketing", "HR", "Product", "Sales", "Finance"])
    st.caption("Ask questions about the organization. Answers include evidence and confidence scores.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("evidence"):
                with st.expander("Evidence"):
                    for ev in msg["evidence"]:
                        st.markdown(f"• **{ev.get('type', '')}** — {ev.get('summary', '')[:120]}")
                st.caption(f"Confidence: {msg.get('confidence', 0)*100:.0f}%")

    question = st.chat_input("Ask about the organization...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        agent = get_agent(role, memory)
        result = agent.ask(question)
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "evidence": result["evidence"],
            "confidence": result["confidence"],
        })
        st.rerun()

    with st.expander("Example Questions"):
        st.markdown("""
        - What is blocking Payments?
        - What is happening in the organization?
        - Which projects are at risk?
        - What changed this week?
        - What campaigns are delayed?
        - Who is working on Payments?
        - What decisions were made?
        - What duplicate work exists?
        """)


# --- Daily Brief ---
elif page == "Daily Brief":
    st.title("Daily Organizational Brief")
    if st.button("Generate Brief"):
        with st.spinner("Generating..."):
            brief = generate_daily_brief()
        st.text_area("Briefing", brief, height=500)
    else:
        row = query("SELECT content FROM daily_briefs ORDER BY brief_date DESC LIMIT 1")
        if row:
            st.text_area("Latest Briefing", row[0]["content"], height=500)
        else:
            st.info("Click 'Generate Brief' to create the daily organizational briefing.")
