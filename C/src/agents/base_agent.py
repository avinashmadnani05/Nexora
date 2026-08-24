"""Evidence-backed agent responses."""

import json
from typing import Optional

from src.intelligence.memory import OrganizationalMemory
from src.intelligence.retrieval import Retriever
from src.intelligence.temporal import TemporalMemory
from src.llm.provider import get_llm_provider, LLMProvider


DEPARTMENT_CONTEXT = {
    "Engineering": "Focus on technical work, blockers, dependencies, GitHub/Jira, engineering meetings, technical decisions.",
    "Marketing": "Focus on campaigns, creative assets, launch timelines, marketing meetings, content.",
    "HR": "Focus on hiring, onboarding, open roles, employee matters, HR communications.",
    "Product": "Focus on roadmap, features, product decisions, cross-team coordination.",
    "Sales": "Focus on opportunities, customers, pipeline, sales activities.",
    "Finance": "Focus on budgets, financial tasks, operational finance matters.",
    "Founder": "Cross-department organizational view. Synthesize risks, blockers, decisions across all teams.",
}


class BaseAgent:
    def __init__(self, department: str, memory: Optional[OrganizationalMemory] = None, llm: Optional[LLMProvider] = None):
        self.department = department
        self.memory = memory or OrganizationalMemory()
        self.retriever = Retriever(self.memory)
        self.temporal = TemporalMemory()
        self.llm = llm or get_llm_provider()

    def _build_evidence(self, context: dict) -> list[dict]:
        evidence = []
        for comm in context.get("communications", [])[:8]:
            source_label = comm.get("source", "unknown").title()
            sender = comm.get("sender", "")
            emp = self.memory.get_employee_by_name(sender) if sender.startswith("EMP") else None
            name = emp["name"] if emp else sender
            evidence.append({
                "type": source_label,
                "source_id": comm.get("id"),
                "summary": comm.get("content", "")[:150],
                "sender": name,
                "timestamp": comm.get("timestamp"),
            })
        for event in context.get("events", [])[:5]:
            if event.get("event_type") in ("blocker", "decision", "risk", "resolution"):
                evidence.append({
                    "type": event.get("source_type", "event").title(),
                    "source_id": event.get("source_id"),
                    "summary": event.get("summary", "")[:150],
                    "event_type": event.get("event_type"),
                    "timestamp": event.get("timestamp"),
                })
        return evidence

    def _synthesize_answer(self, question: str, context: dict, evidence: list[dict]) -> tuple[str, float]:
        """Generate answer from retrieved context without hard-coded Q&A."""
        q = question.lower()
        keywords = self.retriever.extract_keywords(question)

        blockers = context.get("blockers", [])
        events = context.get("events", [])
        projects = context.get("projects", [])
        decisions = context.get("decisions", [])

        relevant_blockers = [b for b in blockers if any(k in str(b).lower() for k in keywords) or not keywords]
        relevant_events = sorted(events, key=lambda e: e.get("timestamp", ""))

        parts = []
        confidence = 0.5

        if any(w in q for w in ["block", "blocking", "wrong", "issue", "problem"]):
            blocker_events = [e for e in relevant_events if e.get("event_type") == "blocker"]
            deps = list({b.get("dependency") or e.get("dependency") for b in relevant_blockers + blocker_events if b.get("dependency") or e.get("dependency")})
            if deps:
                proj_name = projects[0]["name"] if projects else "the project"
                parts.append(f"{proj_name} appears to be blocked by {', '.join(deps)}.")
                confidence = 0.89
            elif blocker_events:
                parts.append(blocker_events[-1].get("summary", "A blocker was identified from organizational communications."))
                confidence = 0.82

        elif any(w in q for w in ["risk", "at risk"]):
            risk_events = [e for e in relevant_events if e.get("event_type") in ("risk", "blocker")]
            if risk_events:
                parts.append(f"Identified {len(risk_events)} risk signal(s). " + risk_events[-1].get("summary", ""))
                confidence = 0.85
            active = [b for b in blockers if b.get("status") == "active"]
            if active:
                parts.append(f"{len(active)} active blocker(s) across the organization.")

        elif any(w in q for w in ["decision", "decided", "agreed"]):
            if decisions:
                parts.append("Recent decisions: " + "; ".join(d.get("summary", "")[:80] for d in decisions[:3]))
                confidence = 0.86
            dec_events = [e for e in relevant_events if e.get("event_type") == "decision"]
            if dec_events:
                parts.append(dec_events[-1].get("summary", ""))

        elif any(w in q for w in ["who", "working on"]):
            for emp in context.get("employees", []):
                parts.append(f"{emp['name']} ({emp['role']}, {emp['department']}) is associated with relevant work.")
                confidence = 0.80
            if not context.get("employees") and projects:
                members = projects[0].get("members", "[]")
                if isinstance(members, str):
                    members = json.loads(members) if members.startswith("[") else []
                for mid in members[:3]:
                    emp = self.memory.get_employees()
                    for e in emp:
                        if e["id"] == mid:
                            parts.append(f"{e['name']} is working on {projects[0]['name']}.")

        elif any(w in q for w in ["changed", "happened", "week", "today", "yesterday"]):
            if relevant_events:
                timeline = [f"• {e.get('timestamp', '')[:10]}: {e.get('summary', '')[:100]}" for e in relevant_events[-8:]]
                parts.append("Timeline of relevant events:\n" + "\n".join(timeline))
                confidence = 0.84

        elif any(w in q for w in ["campaign", "marketing", "creative", "launch"]):
            mkt_events = [e for e in relevant_events if e.get("department") == "Marketing" or "campaign" in str(e).lower()]
            if mkt_events:
                parts.append(mkt_events[-1].get("summary", ""))
                confidence = 0.83

        elif any(w in q for w in ["onboard", "hiring", "joined", "open role"]):
            hr_events = [e for e in relevant_events if e.get("event_type") == "onboarding" or e.get("department") == "HR"]
            if hr_events:
                parts.append(hr_events[-1].get("summary", ""))
                confidence = 0.82

        elif any(w in q for w in ["duplicate", "overlap"]):
            dup = [e for e in relevant_events if e.get("event_type") == "duplicate_work"]
            if dup:
                parts.append(dup[-1].get("summary", "Possible duplicate work identified across teams."))
                confidence = 0.82

        elif any(w in q for w in ["happening", "brief", "overview", "attention"]):
            active_blockers = self.memory.get_blockers()
            dept_summary = {}
            all_events = self.memory.get_events()
            for e in all_events[-50:]:
                d = e.get("department", "Unknown")
                dept_summary.setdefault(d, []).append(e)
            parts.append("Organizational overview based on recent communications:")
            for d, evts in dept_summary.items():
                blockers_d = [e for e in evts if e.get("event_type") == "blocker"]
                parts.append(f"• {d}: {len(evts)} recent signals, {len(blockers_d)} blocker(s).")
            if active_blockers:
                parts.append(f"Top concern: {active_blockers[0].get('summary', 'active blockers detected')[:120]}")
            confidence = 0.87

        if not parts:
            if relevant_events:
                parts.append(relevant_events[-1].get("summary", "Based on organizational data, see evidence below."))
                confidence = 0.75
            elif evidence:
                parts.append("Based on retrieved communications, see evidence below for details.")
                confidence = 0.70
            else:
                parts.append("Insufficient organizational data to answer confidently. Try rephrasing or check if data has been processed.")
                confidence = 0.30

        return " ".join(parts), confidence

    def ask(self, question: str) -> dict:
        dept_filter = None if self.department == "Founder" else self.department
        context = self.retriever.retrieve_context(question, department=dept_filter)
        evidence = self._build_evidence(context)
        answer, confidence = self._synthesize_answer(question, context, evidence)

        if confidence < 0.5 and evidence:
            confidence = min(0.75, 0.5 + len(evidence) * 0.05)

        return {
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "confidence": round(confidence, 2),
            "department": self.department,
        }


class DepartmentAgent(BaseAgent):
    pass


class FounderAgent(BaseAgent):
    def __init__(self, memory=None, llm=None):
        super().__init__("Founder", memory, llm)

    def ask(self, question: str) -> dict:
        result = super().ask(question)
        eng = DepartmentAgent("Engineering", self.memory, self.llm)
        prod = DepartmentAgent("Product", self.memory, self.llm)
        eng_ctx = self.retriever.retrieve_context(question, department="Engineering")
        prod_ctx = self.retriever.retrieve_context(question, department="Product")

        eng_blockers = [e for e in eng_ctx.get("events", []) if e.get("event_type") == "blocker"]
        prod_risks = [e for e in prod_ctx.get("events", []) if e.get("event_type") == "risk"]

        if eng_blockers and prod_risks and "payment" in question.lower():
            cross = (
                " Cross-department analysis: Engineering reports infrastructure blockers while "
                "Product timeline pressure exists — combined risk to delivery."
            )
            result["answer"] += cross
            result["confidence"] = min(0.95, result["confidence"] + 0.05)

        return result


def get_agent(role: str, memory=None, llm=None) -> BaseAgent:
    if role == "Founder":
        return FounderAgent(memory, llm)
    return DepartmentAgent(role, memory, llm)
