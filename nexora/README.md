# Nexora Organizational Intelligence

A local Streamlit proof-of-concept for exploring synthetic organizational intelligence. It generates a 60-person fictional company, 12 connected projects, 60 tasks, 30 days of legacy activity, and communication-first source data. Insights are explicitly framed as activity/involvement signals, with supporting evidence and confidence.

## Current Phase

Phase 1 preserves the existing Streamlit dashboard and organization model. Phase 2 adds realistic, linked raw communication sources for the later extraction pipeline:

- `data/gmail.json`: sender, recipients, subject, body, project and task references
- `data/slack.json`: channel messages, thread IDs, reply relationships, project and task references
- `data/meetings.json`: participants, transcripts, dates, departments, and projects

The generated communication intentionally contains discoverable scenarios such as the Payments infrastructure dependency, analytics overlap, campaign delay and recovery, roadmap decisions, onboarding, and knowledge concentration. Extraction, organizational memory, and agent upgrades are the next phases; the existing activity-driven dashboard remains available during this work.

## Run

```powershell
cd nexora
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_demo.py
streamlit run app.py
```

Set `OPENAI_API_KEY` to enable an optional LLM answer path. Without it, Ask Organization AI uses deterministic mock analysis and remains fully functional. The generated JSON under `data/` is the clean workflow/API contract; `database.py` can index activities in SQLite for later n8n integration.
