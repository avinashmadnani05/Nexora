"""Communication preprocessing and normalization."""

import re
from src.models.communication import RawCommunication


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    return text


def normalize_communication(comm: RawCommunication) -> RawCommunication:
    return RawCommunication(
        id=comm.id,
        source=comm.source,
        timestamp=comm.timestamp,
        sender=comm.sender or "",
        content=clean_text(comm.content),
        department=comm.department or "",
        project_id=comm.project_id,
        recipients=comm.recipients,
        channel=comm.channel,
        subject=comm.subject,
        metadata=comm.metadata,
    )


def preprocess_batch(comms: list[RawCommunication]) -> list[RawCommunication]:
    return [normalize_communication(c) for c in comms if c.content]
