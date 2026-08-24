"""LLM provider abstraction."""

from abc import ABC, abstractmethod
import json
import re

from src.utils.config import get_config


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> str:
        pass

    def complete_json(self, prompt: str, system: str = "") -> dict:
        text = self.complete(prompt, system)
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}


class MockProvider(LLMProvider):
    """Deterministic mock provider for demo without API keys."""

    def complete(self, prompt: str, system: str = "") -> str:
        lower = (prompt + system).lower()
        if "extract" in lower or "event" in lower:
            return self._mock_extraction(prompt)
        if "brief" in lower or "briefing" in lower:
            return self._mock_briefing(prompt)
        if "answer" in lower or "question" in lower:
            return self._mock_answer(prompt)
        return '{"status": "ok", "note": "mock response"}'

    def _mock_extraction(self, prompt: str) -> str:
        content = prompt.lower()
        events = []
        if "infra" in content or "infrastructure" in content or "deploy" in content:
            events.append({
                "event_type": "blocker",
                "status": "blocked",
                "dependency": "Infrastructure",
                "confidence": 0.91,
                "summary": "Blocked waiting for infrastructure deployment",
            })
        if "campaign" in content or "creative" in content or "launch" in content:
            events.append({
                "event_type": "risk",
                "status": "delayed",
                "summary": "Campaign launch delayed due to incomplete creative assets",
                "confidence": 0.87,
            })
        if "decided" in content or "agreed" in content or "decision" in content:
            events.append({
                "event_type": "decision",
                "summary": "Technical or product decision recorded",
                "confidence": 0.85,
            })
        if "onboard" in content or "new hire" in content or "welcome" in content:
            events.append({
                "event_type": "onboarding",
                "summary": "Employee onboarding activity",
                "confidence": 0.88,
            })
        if "duplicate" in content or "overlap" in content or "analytics dashboard" in content:
            events.append({
                "event_type": "duplicate_work",
                "summary": "Possible duplicate work on analytics functionality",
                "confidence": 0.82,
            })
        if "completed" in content or "merged" in content or "resolved" in content:
            events.append({
                "event_type": "resolution",
                "status": "resolved",
                "summary": "Issue or task resolved",
                "confidence": 0.90,
            })
        if not events:
            events.append({
                "event_type": "update",
                "summary": "General project update",
                "confidence": 0.70,
            })
        return json.dumps({"events": events})

    def _mock_briefing(self, prompt: str) -> str:
        return json.dumps({
            "briefing": (
                "NEXORA — DAILY BRIEF\n\n"
                "ENGINEERING\n"
                "• Payments deployment dependency unresolved.\n"
                "• 5 tasks completed.\n"
                "• 2 blockers detected.\n\n"
                "MARKETING\n"
                "• Q3 campaign launch moved.\n"
                "• Creative assets incomplete.\n\n"
                "HR\n"
                "• 2 employees onboarding.\n"
                "• Backend Engineer hiring still open.\n\n"
                "TOP RISKS\n"
                "1. Payments infrastructure dependency.\n"
                "2. Q3 campaign delay."
            )
        })

    def _mock_answer(self, prompt: str) -> str:
        return json.dumps({
            "answer": "See evidence from organizational memory.",
            "confidence": 0.85,
        })


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.2
        )
        return response.choices[0].message.content or ""


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str):
        import httpx

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")


def get_llm_provider() -> LLMProvider:
    cfg = get_config()
    provider = cfg["llm_provider"].lower()
    if provider == "openai" and cfg["openai_api_key"]:
        return OpenAIProvider(cfg["openai_api_key"], cfg["model_name"])
    if provider == "ollama":
        return OllamaProvider(cfg["ollama_base_url"], cfg["model_name"])
    return MockProvider()
