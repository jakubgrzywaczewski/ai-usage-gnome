from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional, Callable

from ai_usage.domain.localization import Localizer
from ai_usage.domain.models import DisplayPreferences

logger = logging.getLogger(__name__)


def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".config"
    d = base / "ai-usage"
    d.mkdir(parents=True, exist_ok=True)
    return d


class SettingsStore:
    def __init__(self, config_dir: Optional[Path] = None):
        self._config_dir = config_dir or _config_dir()
        self._file = self._config_dir / "settings.json"
        self._preferences = self._load()
        self._on_change_callbacks: list[Callable] = []

    @property
    def preferences(self) -> DisplayPreferences:
        return self._preferences

    @preferences.setter
    def preferences(self, value: DisplayPreferences) -> None:
        old = self._preferences
        self._preferences = value
        self._persist()
        for cb in self._on_change_callbacks:
            cb(old, value)

    def on_change(self, callback: Callable) -> None:
        self._on_change_callbacks.append(callback)

    @property
    def localizer(self) -> Localizer:
        return Localizer(self._preferences.language)

    @property
    def staleness_threshold(self) -> float:
        return max(float(self._preferences.refresh_interval_minutes * 120), 15 * 60)

    def _load(self) -> DisplayPreferences:
        if not self._file.exists():
            return DisplayPreferences()
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            return DisplayPreferences.from_dict(data)
        except Exception as e:
            logger.warning("Failed to load settings: %s", e)
            return DisplayPreferences()

    def _persist(self) -> None:
        try:
            self._file.write_text(
                json.dumps(self._preferences.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
