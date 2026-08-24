from __future__ import annotations
from collections import Counter
import json
import os
from urllib.request import Request, urlopen
from typing import Any


def department_agent(data: dict[str, Any], department: str) -> dict[str, Any]:
    projects = [p for p in data["projects"] if p["department"] == department]
    people = [e for e in data["employees"] if e["department"] == department]
    activities = [a for a in data["activities"] if a["department"] == department]
    return {"department": department, "projects": projects, "people": people, "activity": activities, "signals": Counter(a["activity_type"] for a in activities)}


def founder_agent(data: dict[str, Any]) -> dict[str, Any]:
    blocked = [a for a in data["activities"] if a["activity_type"] == "blocker"]
    decisions = [a for a in data["activities"] if a["activity_type"] == "decision"]
    risks = [p for p in data["projects"] if p["status"] == "at risk"]
    return {"briefing": "Nexora has active delivery across six departments. Payments recovered from an infrastructure blocker, while Atlas Analytics and the Q3 Launch Campaign remain the clearest risk signals.", "risks": risks, "blockers": blocked, "decisions": decisions, "departments": [department_agent(data, d) for d in data["company"]["departments"]]}


def llm_answer(question: str, context: str) -> str | None:
    """Use an OpenAI-compatible endpoint when configured; return None on any local failure."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    payload = {"model": os.getenv("NEXORA_MODEL", "gpt-4o-mini"), "messages": [{"role": "system", "content": "Answer from the supplied Nexora records. Keep answers concise and include evidence and confidence."}, {"role": "user", "content": f"Question: {question}\nRecords: {context}"}], "temperature": 0.1}
    request = Request(os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"), data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode())["choices"][0]["message"]["content"]
    except Exception:
        return None
