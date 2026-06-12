"""JSON-on-disk queue: draft items, seen tweet ids, daily send counters."""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import DATA_PATH

_EMPTY = {"seen_tweet_ids": [], "sent_log": {}, "items": []}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class Store:
    def __init__(self, path: Path = DATA_PATH):
        self.path = path
        if path.exists():
            self.data = json.loads(path.read_text())
        else:
            self.data = json.loads(json.dumps(_EMPTY))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(self.data, f, indent=2)
        os.replace(tmp, self.path)

    # --- seen tweets ---

    def is_seen(self, tweet_id: str) -> bool:
        return tweet_id in self.data["seen_tweet_ids"]

    def mark_seen(self, tweet_id: str) -> None:
        if not self.is_seen(tweet_id):
            self.data["seen_tweet_ids"].append(tweet_id)

    # --- items ---

    def add_item(self, kind: str, text: str, target: dict | None = None,
                 score: int | None = None, reason: str | None = None) -> dict:
        item = {
            "id": str(uuid.uuid4())[:8],
            "kind": kind,
            "status": "pending",
            "text": text,
            "target": target or {},
            "score": score,
            "reason": reason,
            "created_at": _now(),
            "sent_at": None,
        }
        self.data["items"].append(item)
        return item

    def items(self, status: str | None = None, kind: str | None = None) -> list[dict]:
        out = self.data["items"]
        if status:
            out = [i for i in out if i["status"] == status]
        if kind:
            out = [i for i in out if i["kind"] == kind]
        return out

    def get(self, item_id: str) -> dict | None:
        return next((i for i in self.data["items"] if i["id"] == item_id), None)

    # --- daily caps ---

    def sent_today(self, kind: str) -> int:
        return self.data["sent_log"].get(_today(), {}).get(kind, 0)

    def record_sent(self, item: dict) -> None:
        item["status"] = "sent"
        item["sent_at"] = _now()
        day = self.data["sent_log"].setdefault(_today(), {})
        day[item["kind"]] = day.get(item["kind"], 0) + 1
