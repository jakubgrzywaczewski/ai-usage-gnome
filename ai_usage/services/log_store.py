from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAXIMUM_ENTRIES = 300


@dataclass
class AppLogEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: str = "info"
    category: str = ""
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "level": self.level,
            "category": self.category,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AppLogEntry:
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            timestamp_utc=datetime.fromisoformat(d["timestamp_utc"]) if d.get("timestamp_utc") else datetime.now(timezone.utc),
            level=d.get("level", "info"),
            category=d.get("category", ""),
            message=d.get("message", ""),
        )


class LogStore:
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            from ai_usage.services.settings_store import _config_dir
            config_dir = _config_dir()
        self._file = config_dir / "logs.json"
        self._entries: list[AppLogEntry] = self._load()
        self._on_change_callbacks: list = []

    @property
    def entries(self) -> list[AppLogEntry]:
        return list(self._entries)

    def on_change(self, callback) -> None:
        self._on_change_callbacks.append(callback)

    def append(self, category: str, message: str, level: str = "info") -> None:
        entry = AppLogEntry(level=level, category=category, message=message)
        self._entries.append(entry)
        if len(self._entries) > MAXIMUM_ENTRIES:
            self._entries = self._entries[-MAXIMUM_ENTRIES:]
        self._persist()
        for cb in self._on_change_callbacks:
            cb()

    def clear(self) -> None:
        self._entries.clear()
        self._persist()
        for cb in self._on_change_callbacks:
            cb()

    @property
    def export_text(self) -> str:
        lines = []
        for entry in self._entries:
            ts = entry.timestamp_utc.isoformat()
            lines.append(f"[{ts}] [{entry.level.upper()}] [{entry.category}] {entry.message}")
        return "\n".join(lines)

    def _load(self) -> list[AppLogEntry]:
        if not self._file.exists():
            return []
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            return [AppLogEntry.from_dict(e) for e in data]
        except Exception as e:
            logger.warning("Failed to load logs: %s", e)
            return []

    def _persist(self) -> None:
        try:
            self._file.write_text(
                json.dumps([e.to_dict() for e in self._entries], ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to persist logs: %s", e)
