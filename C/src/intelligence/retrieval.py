"""Retrieval for agent context."""

import re
from typing import Optional

from src.intelligence.memory import OrganizationalMemory


class Retriever:
    def __init__(self, memory: Optional[OrganizationalMemory] = None):
        self.memory = memory or OrganizationalMemory()

    def extract_keywords(self, question: str) -> list[str]:
        stop = {"what", "is", "the", "are", "who", "how", "when", "where", "which", "a", "an", "in", "on", "at", "for", "to", "of", "this", "that", "with", "about", "happening", "changed", "today", "week", "working", "blocked", "blocking", "tell", "me", "give", "show"}
        words = re.findall(r"[a-zA-Z]+", question.lower())
        return [w for w in words if w not in stop and len(w) > 2]

    def retrieve_context(self, question: str, department: Optional[str] = None, limit: int = 15) -> dict:
        keywords = self.extract_keywords(question)
        context = {
            "events": [],
            "communications": [],
            "projects": [],
            "blockers": [],
            "decisions": [],
            "employees": [],
        }

        for kw in keywords:
            proj = self.memory.get_project_by_name(kw)
            if proj and proj not in context["projects"]:
                context["projects"].append(proj)
            emp = self.memory.get_employee_by_name(kw)
            if emp and emp not in context["employees"]:
                context["employees"].append(emp)

        for kw in keywords:
            comms = self.memory.search_communications(kw, limit=5)
            for c in comms:
                if c not in context["communications"]:
                    context["communications"].append(c)

        if department:
            context["events"].extend(self.memory.get_events(department=department)[:limit])
        else:
            for kw in keywords:
                events = self.memory.get_events()
                for e in events:
                    if any(kw in str(v).lower() for v in e.values() if v):
                        if e not in context["events"]:
                            context["events"].append(e)

        if not context["events"]:
            context["events"] = self.memory.get_events(department=department)[:limit]

        context["blockers"] = self.memory.get_blockers(active_only="block" in question.lower() or "risk" in question.lower())
        if not context["blockers"]:
            context["blockers"] = self.memory.get_blockers(active_only=False)[:10]

        context["decisions"] = self.memory.get_decisions(department)[:10]

        if "payment" in question.lower():
            proj = self.memory.get_project_by_name("Payments")
            if proj:
                context["projects"] = [proj]
                context["events"].extend(self.memory.get_events(project_id=proj["id"]))
                context["communications"].extend(self.memory.get_communications_for_project(proj["id"]))

        return context

    def score_relevance(self, item: dict, keywords: list[str]) -> float:
        text = " ".join(str(v) for v in item.values() if v).lower()
        return sum(1 for k in keywords if k in text) / max(len(keywords), 1)
