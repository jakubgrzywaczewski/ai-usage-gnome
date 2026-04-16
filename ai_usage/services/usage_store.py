from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from ai_usage.domain.models import (
    ProviderID,
    ProviderSnapshot,
    UsageAlertState,
)

logger = logging.getLogger(__name__)


class UsageStore:
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            from ai_usage.services.settings_store import _config_dir
            config_dir = _config_dir()
        self._config_dir = config_dir
        self._snapshots_file = config_dir / "snapshots.json"
        self._alerts_file = config_dir / "alerts.json"
        self._markers_file = config_dir / "reset_markers.json"

    def load_snapshots(self) -> dict[ProviderID, ProviderSnapshot]:
        if not self._snapshots_file.exists():
            return {}
        try:
            data = json.loads(self._snapshots_file.read_text(encoding="utf-8"))
            snapshots = [ProviderSnapshot.from_dict(s) for s in data]
            return {s.provider: s for s in snapshots}
        except Exception as e:
            logger.warning("Failed to load snapshots: %s", e)
            return {}

    def save_snapshots(self, snapshots: dict[ProviderID, ProviderSnapshot]) -> None:
        values = sorted(snapshots.values(), key=lambda s: s.provider.value)
        try:
            self._snapshots_file.write_text(
                json.dumps([s.to_dict() for s in values], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save snapshots: %s", e)

    def load_alert_states(self) -> dict[str, UsageAlertState]:
        if not self._alerts_file.exists():
            return {}
        try:
            data = json.loads(self._alerts_file.read_text(encoding="utf-8"))
            return {k: UsageAlertState.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.warning("Failed to load alert states: %s", e)
            return {}

    def save_alert_states(self, states: dict[str, UsageAlertState]) -> None:
        try:
            self._alerts_file.write_text(
                json.dumps({k: v.to_dict() for k, v in states.items()}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save alert states: %s", e)

    def load_reset_markers(self) -> set[str]:
        if not self._markers_file.exists():
            return set()
        try:
            data = json.loads(self._markers_file.read_text(encoding="utf-8"))
            return set(data)
        except Exception as e:
            logger.warning("Failed to load reset markers: %s", e)
            return set()

    def save_reset_markers(self, markers: set[str]) -> None:
        try:
            self._markers_file.write_text(
                json.dumps(sorted(markers), indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save reset markers: %s", e)
