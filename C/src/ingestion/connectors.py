"""Ingestion connector interfaces."""

from abc import ABC, abstractmethod
from typing import Iterator

from src.models.communication import RawCommunication


class IngestionConnector(ABC):
    @abstractmethod
    def fetch(self) -> Iterator[RawCommunication]:
        pass


class SyntheticGmailConnector(IngestionConnector):
    def __init__(self, data_path):
        import json
        from pathlib import Path

        self.path = Path(data_path)

    def fetch(self) -> Iterator[RawCommunication]:
        import json

        if not self.path.exists():
            return
        with open(self.path) as f:
            for item in json.load(f):
                yield RawCommunication(
                    id=item["id"],
                    source="gmail",
                    timestamp=item["timestamp"],
                    sender=item["sender"],
                    recipients=item.get("recipients", []),
                    content=item.get("body", item.get("content", "")),
                    department=item.get("department", ""),
                    project_id=item.get("project_id"),
                    subject=item.get("subject"),
                    metadata={"original": item},
                )


class SyntheticSlackConnector(IngestionConnector):
    def __init__(self, data_path):
        from pathlib import Path

        self.path = Path(data_path)

    def fetch(self) -> Iterator[RawCommunication]:
        import json

        if not self.path.exists():
            return
        with open(self.path) as f:
            for item in json.load(f):
                yield RawCommunication(
                    id=item["id"],
                    source="slack",
                    timestamp=item["timestamp"],
                    sender=item["sender"],
                    channel=item.get("channel"),
                    content=item.get("message", item.get("content", "")),
                    department=item.get("department", ""),
                    project_id=item.get("project_id"),
                    metadata={"thread_id": item.get("thread_id"), "original": item},
                )


class SyntheticMeetingConnector(IngestionConnector):
    def __init__(self, data_path):
        from pathlib import Path

        self.path = Path(data_path)

    def fetch(self) -> Iterator[RawCommunication]:
        import json

        if not self.path.exists():
            return
        with open(self.path) as f:
            for item in json.load(f):
                yield RawCommunication(
                    id=item["id"],
                    source="meeting",
                    timestamp=item.get("date", item.get("timestamp", "")),
                    sender="meeting",
                    content=item.get("transcript", ""),
                    department=item.get("department", ""),
                    project_id=item.get("project_id"),
                    metadata={"participants": item.get("participants", []), "original": item},
                )


class SyntheticJiraConnector(IngestionConnector):
    def __init__(self, data_path):
        from pathlib import Path

        self.path = Path(data_path)

    def fetch(self) -> Iterator[RawCommunication]:
        import json

        if not self.path.exists():
            return
        with open(self.path) as f:
            for item in json.load(f):
                yield RawCommunication(
                    id=item["id"],
                    source="jira",
                    timestamp=item["timestamp"],
                    sender=item.get("assignee", ""),
                    content=item.get("comment", item.get("summary", "")),
                    department=item.get("department", ""),
                    project_id=item.get("project_id"),
                    metadata={"task_id": item.get("task_id"), "status": item.get("status"), "original": item},
                )


def ingest_all(generated_dir) -> list[RawCommunication]:
    from pathlib import Path

    base = Path(generated_dir)
    connectors = [
        SyntheticGmailConnector(base / "gmail.json"),
        SyntheticSlackConnector(base / "slack.json"),
        SyntheticMeetingConnector(base / "meetings.json"),
        SyntheticJiraConnector(base / "jira.json"),
    ]
    comms = []
    for c in connectors:
        comms.extend(list(c.fetch()))
    comms.sort(key=lambda x: x.timestamp)
    return comms
