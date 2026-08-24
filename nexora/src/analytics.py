from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta
from typing import Any


def activity_counts(activities: list[dict[str, Any]], day: int | None = None) -> Counter:
    selected = activities if day is None else [a for a in activities if int(a["timestamp"][8:10]) >= 23 + day]
    return Counter(a["activity_type"] for a in selected)


def timeline(activities: list[dict[str, Any]], day: int) -> list[dict[str, Any]]:
    start = min(datetime.fromisoformat(a["timestamp"]) for a in activities)
    cutoff = start + timedelta(days=day - 1, hours=23, minutes=59, seconds=59)
    return [a for a in activities if datetime.fromisoformat(a["timestamp"]) <= cutoff]
