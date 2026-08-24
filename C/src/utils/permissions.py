"""Role-based access control for POC."""

ALLOWED_DEPARTMENTS = {
    "Founder": ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance"],
    "Engineering": ["Engineering"],
    "Marketing": ["Marketing"],
    "HR": ["HR"],
    "Product": ["Product"],
    "Sales": ["Sales"],
    "Finance": ["Finance"],
}


def can_access_department(role: str, department: str) -> bool:
    allowed = ALLOWED_DEPARTMENTS.get(role, [])
    return department in allowed or role == "Founder"


def filter_evidence_for_role(role: str, evidence: list[dict]) -> list[dict]:
    if role == "Founder":
        return evidence
    return evidence
