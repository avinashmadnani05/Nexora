"""End-to-end tests for Nexora platform."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.generator import generate_all, generate_employees, generate_communications
from src.ingestion.connectors import ingest_all
from src.processing.preprocessor import preprocess_batch
from src.processing.extractor import extract_all, _rule_based_extract
from src.models.communication import RawCommunication
from src.models.database import init_db, clear_all_data, query
from src.intelligence.memory import OrganizationalMemory
from src.intelligence.temporal import TemporalMemory
from src.agents.base_agent import get_agent, FounderAgent
from src.utils.config import GENERATED_DIR


@pytest.fixture(scope="module")
def setup_data():
    init_db()
    clear_all_data()
    org = generate_all(GENERATED_DIR)
    memory = OrganizationalMemory()
    memory.load_organization(org)
    comms = ingest_all(GENERATED_DIR)
    comms = preprocess_batch(comms)
    import json
    raw_rows = []
    for c in comms:
        d = c.to_dict()
        d["recipients"] = json.dumps(d.get("recipients") or [])
        d["metadata"] = json.dumps(d.get("metadata") or {})
        raw_rows.append(d)
    memory.store_raw_communications(raw_rows)
    events = extract_all(comms, employees=org["employees"], projects=org["projects"])
    memory.store_events(events)
    temporal = TemporalMemory()
    temporal.build_snapshots()
    return {"org": org, "comms": comms, "events": events, "memory": memory}


def test_generate_employees():
    emps = generate_employees(60)
    assert len(emps) == 60
    assert all(e["department"] in ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance"] for e in emps)


def test_generate_communications_connected():
    emps = generate_employees(60)
    from src.ingestion.generator import generate_projects
    projects = generate_projects(emps)
    comms = generate_communications(emps, projects)
    assert len(comms["slack"]) > 50
    slack_text = " ".join(m["message"] for m in comms["slack"])
    assert "infra" in slack_text.lower() or "infrastructure" in slack_text.lower() or "blocked" in slack_text.lower()


def test_ingestion(setup_data):
    assert len(setup_data["comms"]) > 100


def test_extraction_finds_blocker(setup_data):
    comms = setup_data["comms"]
    infra_comms = [c for c in comms if "infra" in c.content.lower() or "blocked" in c.content.lower()]
    assert len(infra_comms) > 0
    events = extract_all(infra_comms[:5], employees=setup_data["org"]["employees"], projects=setup_data["org"]["projects"])
    blocker_events = [e for e in events if e.get("event_type") == "blocker" or e.get("dependency")]
    assert len(blocker_events) > 0


def test_database_storage(setup_data):
    employees = query("SELECT * FROM employees")
    events = query("SELECT * FROM organizational_events")
    assert len(employees) == 60
    assert len(events) > 0


def test_temporal_snapshots(setup_data):
    snapshots = query("SELECT * FROM daily_snapshots")
    assert len(snapshots) >= 6


def test_payments_blocker_question(setup_data):
    agent = get_agent("Founder", setup_data["memory"])
    result = agent.ask("What is blocking Payments?")
    answer_lower = result["answer"].lower()
    assert "infra" in answer_lower or "block" in answer_lower or "deploy" in answer_lower
    assert result["confidence"] > 0.5
    assert len(result["evidence"]) > 0


def test_payments_timeline_question(setup_data):
    agent = get_agent("Engineering", setup_data["memory"])
    result = agent.ask("What happened with Payments this week?")
    assert len(result["answer"]) > 20
    assert result["confidence"] > 0.5


def test_founder_cross_department(setup_data):
    agent = FounderAgent(setup_data["memory"])
    result = agent.ask("Is Payments at risk?")
    assert len(result["answer"]) > 10


def test_marketing_campaign(setup_data):
    agent = get_agent("Marketing", setup_data["memory"])
    result = agent.ask("Which campaigns are delayed?")
    answer = result["answer"].lower()
    assert "campaign" in answer or "creative" in answer or "launch" in answer or len(result["evidence"]) > 0


def test_rule_based_extraction():
    comm = RawCommunication(
        id="TEST-1", source="slack", timestamp="2026-08-01T10:00:00",
        sender="EMP-001", content="Still waiting for infra to deploy the webhook changes before I can finish this.",
        department="Engineering", project_id="PRJ-001",
    )
    events = _rule_based_extract(comm, {"EMP-001": {"name": "Rahul"}}, {"PRJ-001": {"name": "Payments Platform"}})
    assert any(e.get("event_type") == "blocker" for e in events)
    assert any(e.get("dependency") == "Infrastructure" for e in events)
