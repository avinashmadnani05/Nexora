# Nexora — Organizational Intelligence Platform

Nexora is an AI-powered **Organizational Intelligence Platform** proof-of-concept. It ingests organizational communication (Gmail, Slack, meetings, Jira), preprocesses it into structured data, extracts people/projects/tasks/decisions/blockers/dependencies, builds organizational memory, and exposes this knowledge through department-specific AI assistants and a company-wide Founder agent.

## Why This Exists

Organizational communication contains valuable signals about what is actually happening inside a company. Nexora demonstrates how fragmented messages can be synthesized into actionable organizational intelligence — with **evidence-backed answers**, not guesswork.

## Architecture

```text
                SYNTHETIC / REAL DATA
                         │
                         ↓
                 INGESTION LAYER
                         │
                         ↓
                  RAW DATA STORE
                         │
                         ↓
                PROCESSING ENGINE
                         │
                         ↓
              ENTITY / EVENT EXTRACTION
                         │
                         ↓
             ORGANIZATIONAL MEMORY
                         │
                ┌────────┴─────────┐
                ↓                  ↓
       Department Agents      Founder Agent
                │                  │
                └────────┬─────────┘
                         ↓
                    CHAT / UI
```

## Data Flow

1. **Generate** — Synthetic Nexora Technologies org (60 employees, 12 projects, 30 days of communication)
2. **Ingest** — Gmail, Slack, meetings, Jira → unified raw communication model
3. **Preprocess** — Clean and normalize text
4. **Extract** — LLM + rule-based fallback → organizational events
5. **Store** — SQLite organizational memory + temporal snapshots
6. **Query** — Department/Founder agents retrieve context and answer with evidence

## AI Architecture

- **LLMProvider** abstraction with `MockProvider`, `OpenAIProvider`, `OllamaProvider`
- Works **without API keys** in deterministic mock mode
- Retrieval over communications, events, projects, blockers — not full DB dumps
- Confidence scores and evidence citations on every answer

## Department Agents

| Agent | Focus |
|-------|-------|
| Engineering | Blockers, dependencies, technical decisions, Jira/GitHub |
| Marketing | Campaigns, creative delays, launch timelines |
| HR | Hiring, onboarding, open roles |
| Product | Roadmap, features, cross-team coordination |
| Sales | Pipeline, opportunities, customer activity |
| Finance | Budgets, financial operations |
| **Founder** | Cross-department synthesis, org-wide risks |

## Synthetic Data

Fictional company **Nexora Technologies** with 6 departments and semantically connected scenarios:

1. **Payments infrastructure blocker** — webhook work blocked by infra deployment
2. **Marketing campaign delay** — creative assets incomplete
3. **Duplicate analytics work** — Engineering + Product overlap
4. **Technical decision** — async processing for Payments
5. **HR onboarding** — new hire activity across channels
6. **Project recovery** — API Gateway at risk then recovered
7. **Knowledge concentration** — single person owns critical system

## n8n Workflows

Import from `n8n/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `01_process_communications.json` | Trigger → preprocess → extract → store |
| `02_daily_brief.json` | Daily trigger → generate brief |
| `03_chat_request.json` | Webhook → agent → response |

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Full demo setup (generate + process)
python scripts/setup_demo.py

# Or step by step:
python scripts/generate_demo.py
python scripts/process_data.py

# Launch dashboard
streamlit run app.py
```

## Configuration

Copy `.env.example` to `.env`:

```env
LLM_PROVIDER=mock          # mock | openai | ollama
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=gpt-4o-mini
DATABASE_URL=sqlite:///database/nexora.db
```

Set `LLM_PROVIDER=openai` with a valid key for real LLM extraction.

## Demo Scenarios & Example Questions

**Founder:**
- What is happening in the organization?
- Which projects are at risk?
- What is blocking Engineering?
- What changed this week?
- Give me today's organizational briefing.

**Engineering:**
- What is blocking Payments?
- What happened with Payments this week?
- What technical decisions were made?

**Marketing:**
- Which campaigns are delayed?
- What issues were discussed?

**HR:**
- Who is onboarding?
- What hiring activity is happening?

## Dashboard Pages

1. **Organization Overview** — employees, projects, blockers, at-risk projects
2. **Department Intelligence** — per-department insights
3. **Projects** — progress, communications, blockers, timeline
4. **People** — work involvement signals (not productivity scores)
5. **Communication Timeline** — raw comm → events flow
6. **AI Insights** — blockers, decisions, duplicate work, knowledge concentration
7. **Chat** — evidence-backed Q&A with any agent
8. **Daily Brief** — generated organizational briefing

## Testing

```bash
pytest tests/ -v
```

End-to-end test verifies: generate → process → extract → ask "What is blocking Payments?" → infrastructure dependency found.

## Future Real Integrations

Clean connector interfaces ready for:

- `Gmail API`, `Slack API`, `Microsoft Teams`
- `Google Calendar`, `Microsoft Calendar`
- `GitHub`, `Jira`, `Notion`, `Confluence`

Replace `SyntheticGmailConnector` etc. with real implementations — same `IngestionConnector` interface.

## Privacy Considerations

- Role-based department access (`src/utils/permissions.py`)
- Audit logging for queries
- Evidence references — conclusions link to source communications
- **No employee productivity scores** — uses "work involvement signals" instead
- Designed for project/blocker/risk intelligence, not surveillance

## Project Structure

```text
nexora/
├── app.py                    # Streamlit dashboard
├── requirements.txt
├── .env.example
├── data/raw|processed|generated/
├── database/nexora.db
├── src/
│   ├── models/               # Database + communication models
│   ├── ingestion/            # Connectors + synthetic generator
│   ├── processing/           # Preprocess + extraction
│   ├── intelligence/         # Memory, temporal, retrieval
│   ├── agents/               # Department + Founder agents
│   ├── llm/                  # LLM provider abstraction
│   └── analytics/            # Insights
├── scripts/                  # generate_demo, process_data, setup_demo
├── n8n/workflows/
└── tests/
```

## Known Limitations (POC)

- SQLite only (PostgreSQL/pgvector ready schema design)
- Mock LLM uses rule-based extraction (OpenAI/Ollama optional)
- Synthetic data only — no real OAuth connectors
- Simple keyword retrieval (no vector DB yet)
- n8n workflows require local n8n instance

## Recommended Next Steps

1. Connect real Gmail/Slack via OAuth connectors
2. Migrate to PostgreSQL + pgvector for semantic search
3. Add real-time ingestion webhooks
4. Implement fine-grained RBAC per data source
5. Deploy n8n workflows for scheduled processing
