"""Unified raw communication model."""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RawCommunication:
    id: str
    source: str
    timestamp: str
    sender: str
    content: str
    department: str
    project_id: Optional[str] = None
    recipients: Optional[list] = None
    channel: Optional[str] = None
    subject: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "RawCommunication":
        return cls(
            id=data["id"],
            source=data["source"],
            timestamp=data["timestamp"],
            sender=data.get("sender", ""),
            content=data.get("content", ""),
            department=data.get("department", ""),
            project_id=data.get("project_id"),
            recipients=data.get("recipients"),
            channel=data.get("channel"),
            subject=data.get("subject"),
            metadata=data.get("metadata"),
        )
