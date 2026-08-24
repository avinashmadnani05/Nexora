"""End-to-end data processing pipeline."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.connectors import ingest_all
from src.ingestion.generator import generate_all
from src.intelligence.memory import OrganizationalMemory
from src.intelligence.temporal import TemporalMemory
from src.llm.provider import get_llm_provider
from src.models.database import init_db, clear_all_data
from src.processing.extractor import extract_all
from src.processing.preprocessor import preprocess_batch
from src.utils.config import GENERATED_DIR, PROCESSED_DIR, RAW_DIR


def run_pipeline():
    print("Initializing database...")
    init_db()
    clear_all_data()

    print("Generating synthetic organization...")
    org_data = generate_all(GENERATED_DIR)

    print("Loading organization into memory...")
    memory = OrganizationalMemory()
    memory.load_organization(org_data)
    memory.store_meetings(org_data.get("meetings", []))

    print("Ingesting communications...")
    comms = ingest_all(GENERATED_DIR)
    comms = preprocess_batch(comms)

    raw_rows = []
    for c in comms:
        d = c.to_dict()
        d["recipients"] = json.dumps(d.get("recipients") or [])
        d["metadata"] = json.dumps(d.get("metadata") or {})
        raw_rows.append(d)
    memory.store_raw_communications(raw_rows)

    with open(RAW_DIR / "communications.json", "w") as f:
        json.dump([c.to_dict() for c in comms], f, indent=2)

    print(f"Extracting events from {len(comms)} communications...")
    llm = get_llm_provider()
    events = extract_all(comms, llm, org_data["employees"], org_data["projects"])
    memory.store_events(events)

    with open(PROCESSED_DIR / "events.json", "w") as f:
        json.dump(events, f, indent=2)

    print("Building temporal snapshots...")
    temporal = TemporalMemory()
    temporal.build_snapshots()

    print(f"Pipeline complete: {len(comms)} communications, {len(events)} events extracted.")
    return {"communications": len(comms), "events": len(events)}


if __name__ == "__main__":
    run_pipeline()
