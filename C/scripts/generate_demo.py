"""Generate demo data only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.generator import generate_all
from src.models.database import init_db
from src.utils.config import GENERATED_DIR


def main():
    init_db()
    data = generate_all(GENERATED_DIR)
    print(f"Generated Nexora Technologies demo data in {GENERATED_DIR}")
    print(f"  Employees: {len(data['employees'])}")
    print(f"  Projects: {len(data['projects'])}")
    print(f"  Tasks: {len(data['tasks'])}")
    print(f"  Gmail: {len(data['gmail'])}")
    print(f"  Slack: {len(data['slack'])}")
    print(f"  Meetings: {len(data['meetings'])}")
    print(f"  Jira: {len(data['jira'])}")


if __name__ == "__main__":
    main()
