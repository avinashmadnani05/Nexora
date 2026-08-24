"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GENERATED_DIR = DATA_DIR / "generated"
DATABASE_DIR = ROOT_DIR / "database"

for d in (RAW_DIR, PROCESSED_DIR, GENERATED_DIR, DATABASE_DIR):
    d.mkdir(parents=True, exist_ok=True)


def get_config() -> dict:
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "mock"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "database_url": os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR / 'nexora.db'}"),
        "root_dir": str(ROOT_DIR),
    }
