from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.generator import generate_demo_data

if __name__ == "__main__":
    data = generate_demo_data(ROOT / "data")
    print(f"Generated {len(data['employees'])} employees, {len(data['projects'])} projects, {len(data['tasks'])} tasks and {len(data['activities'])} activities.")
