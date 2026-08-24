"""Entity and event extraction from communications."""

import json
import re
import uuid
from typing import Optional

from src.llm.provider import LLMProvider, MockProvider
from src.models.communication import RawCommunication


EXTRACTION_SYSTEM = """You extract structured organizational events from workplace communication.
Return JSON with an "events" array. Each event has: event_type, summary, status, dependency, confidence.
event_type can be: blocker, decision, risk, update, resolution, onboarding, duplicate_work, collaboration.
Do not invent facts not present in the text."""


def _rule_based_extract(comm: RawCommunication, employee_map: dict, project_map: dict) -> list[dict]:
    """Deterministic fallback extraction."""
    text = comm.content.lower()
    events = []
    person = employee_map.get(comm.sender, {}).get("name", comm.sender)
    project = project_map.get(comm.project_id, {}).get("name", comm.project_id)

    patterns = [
        (r"block(ed|ing|er)|waiting for|can't push|pending", "blocker", "blocked"),
        (r"decided|agreed|decision|confirmed", "decision", "decided"),
        (r"delay|behind schedule|push.*launch|moved|incomplete", "risk", "delayed"),
        (r"resolved|completed|merged|unblocked|done|fix deployed", "resolution", "resolved"),
        (r"onboard|welcome|new hire|orientation", "onboarding", "active"),
        (r"duplicate|overlap|also building", "duplicate_work", "identified"),
        (r"single point|only.* knows|only I have", "risk", "knowledge_concentration"),
        (r"at risk|timeline at risk|failing", "risk", "at_risk"),
    ]

    for pattern, event_type, status in patterns:
        if re.search(pattern, text):
            dependency = None
            if "infra" in text or "infrastructure" in text or "staging" in text:
                dependency = "Infrastructure"
            summary = comm.content[:200]
            events.append({
                "event_type": event_type,
                "person": person,
                "department": comm.department,
                "project_id": comm.project_id,
                "project": project,
                "summary": summary,
                "status": status,
                "dependency": dependency,
                "confidence": 0.85 if dependency else 0.75,
                "source_type": comm.source,
                "source_id": comm.id,
                "timestamp": comm.timestamp,
            })

    if not events and len(comm.content) > 20:
        events.append({
            "event_type": "update",
            "person": person,
            "department": comm.department,
            "project_id": comm.project_id,
            "project": project,
            "summary": comm.content[:200],
            "status": "active",
            "dependency": None,
            "confidence": 0.60,
            "source_type": comm.source,
            "source_id": comm.id,
            "timestamp": comm.timestamp,
        })

    return events


def extract_events(
    comm: RawCommunication,
    llm: Optional[LLMProvider] = None,
    employee_map: Optional[dict] = None,
    project_map: Optional[dict] = None,
) -> list[dict]:
    employee_map = employee_map or {}
    project_map = project_map or {}
    llm = llm or MockProvider()

    prompt = f"""Extract organizational events from this communication:

Source: {comm.source}
Department: {comm.department}
Project: {comm.project_id}
Sender: {comm.sender}
Content: {comm.content}

Return JSON with events array."""

    try:
        result = llm.complete_json(prompt, EXTRACTION_SYSTEM)
        events = result.get("events", [])
        for e in events:
            e.setdefault("person", employee_map.get(comm.sender, {}).get("name", comm.sender))
            e.setdefault("department", comm.department)
            e.setdefault("project_id", comm.project_id)
            e.setdefault("source_type", comm.source)
            e.setdefault("source_id", comm.id)
            e.setdefault("timestamp", comm.timestamp)
            e.setdefault("confidence", 0.7)
    except Exception:
        events = []

    if not events:
        events = _rule_based_extract(comm, employee_map, project_map)

    for e in events:
        e["id"] = e.get("id") or f"EVT-{uuid.uuid4().hex[:8]}"

    return events


def extract_all(
    comms: list[RawCommunication],
    llm: Optional[LLMProvider] = None,
    employees: Optional[list] = None,
    projects: Optional[list] = None,
) -> list[dict]:
    employee_map = {e["id"]: e for e in (employees or [])}
    project_map = {p["id"]: p for p in (projects or [])}
    all_events = []
    for comm in comms:
        all_events.extend(extract_events(comm, llm, employee_map, project_map))
    return all_events
