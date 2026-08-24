"""Run full demo setup: generate + process."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.generate_demo import main as generate
from scripts.process_data import run_pipeline


def main():
    generate()
    run_pipeline()
    print("\nDemo ready. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
