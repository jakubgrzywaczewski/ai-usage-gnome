from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from ai_usage.domain.models import (
    MetricUnit,
    ProviderAuthState,
    ProviderFetchState,
    ProviderID,
    ProviderSnapshot,
    UsageMetric,
    UsageMetricKind,
)
from ai_usage.services.log_store import LogStore


USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
FALLBACK_USER_AGENT = "claude-code/2.1.0"


@dataclass
class ClaudeOAuthCredentials:
    access_token: str
    expires_at: Optional[datetime] = None
    scopes: list[str] = None
    rate_limit_tier: Optional[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []

    @property
    def has_usage_scope(self) -> bool:
        return "user:profile" in self.scopes

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at


class ClaudeAuthError(Exception):
    pass


def _load_credentials() -> ClaudeOAuthCredentials:
    data = _load_from_file()
    if data is None:
        raise ClaudeAuthError("Claude Code auth was not found. Run `claude` and refresh.")
    return _parse_credentials(data)


def _load_from_file() -> Optional[dict]:
    env = os.environ
    config_dir_raw = env.get("CLAUDE_CONFIG_DIR", "")
    first_segment = config_dir_raw.split(",")[0].strip() if config_dir_raw else ""

    if first_segment:
        root = Path(first_segment)
    else:
        root = Path.home() / ".claude"

    cred_file = root / ".credentials.json"
    if not cred_file.exists():
        return None

    try:
        return json.loads(cred_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_credentials(data: dict) -> ClaudeOAuthCredentials:
    oauth = data.get("claudeAiOauth")
    if oauth is None:
        raise ClaudeAuthError("Claude Code auth is missing OAuth data. Run `claude` again.")

    access_token = (oauth.get("accessToken") or "").strip()
    if not access_token:
        raise ClaudeAuthError("Claude Code auth is missing an access token. Run `claude` again.")

    expires_at_ms = oauth.get("expiresAt")
    expires_at = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc) if expires_at_ms else None
    scopes = oauth.get("scopes") or []
    rate_limit_tier = oauth.get("rateLimitTier")

    return ClaudeOAuthCredentials(
        access_token=access_token,
        expires_at=expires_at,
        scopes=scopes,
        rate_limit_tier=rate_limit_tier,
    )


def _parse_reset_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc) if "Z" in fmt else datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_usage_metrics(data: dict, now: datetime) -> list[UsageMetric]:
    def _metric(kind: UsageMetricKind, window: Optional[dict]) -> UsageMetric:
        if window is None:
            return UsageMetric(kind=kind, last_updated_at_utc=now)

        utilization = window.get("utilization")
        if utilization is not None:
            utilization = max(0.0, min(1.0, utilization))
            remaining = max(0.0, min(1.0, 1.0 - utilization))
        else:
            remaining = None

        return UsageMetric(
            kind=kind,
            remaining_fraction=remaining,
            remaining_value=remaining,
            total_value=1.0 if utilization is not None else None,
            unit=MetricUnit.PERCENTAGE,
            reset_at_utc=_parse_reset_date(window.get("resets_at")),
            last_updated_at_utc=now,
            detail_text=f"{int(remaining * 100)}% remaining" if remaining is not None else None,
        )

    weekly_window = data.get("seven_day") or data.get("seven_day_oauth_apps")
    return [
        _metric(UsageMetricKind.CLAUDE_FIVE_HOUR, data.get("five_hour")),
        _metric(UsageMetricKind.CLAUDE_WEEKLY, weekly_window),
    ]


class ClaudeProvider:
    id = ProviderID.CLAUDE
    source_description = "Local Claude Code OAuth auth"

    def __init__(self, log_store: LogStore):
        self._log_store = log_store

    def current_auth_state(self) -> ProviderAuthState:
        try:
            _load_credentials()
            return ProviderAuthState.CONFIGURED
        except ClaudeAuthError:
            return ProviderAuthState.SIGNED_OUT

    def clear_auth(self) -> None:
        pass

    def refresh(self, now: datetime) -> ProviderSnapshot:
        base_metrics = [
            UsageMetric(kind=UsageMetricKind.CLAUDE_FIVE_HOUR, last_updated_at_utc=now),
            UsageMetric(kind=UsageMetricKind.CLAUDE_WEEKLY, last_updated_at_utc=now),
        ]

        try:
            creds = _load_credentials()
            if not creds.has_usage_scope:
                raise ClaudeAuthError("Claude Code auth is missing the scope needed for usage data.")
            if creds.is_expired:
                raise ClaudeAuthError("Claude Code auth expired. Run `claude` again and refresh.")

            resp = requests.get(
                USAGE_URL,
                headers={
                    "Authorization": f"Bearer {creds.access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "anthropic-beta": "oauth-2025-04-20",
                    "User-Agent": FALLBACK_USER_AGENT,
                },
                timeout=30,
            )
            self._log_store.append(category="claude", message=f"HTTP {resp.status_code} for {USAGE_URL}")

            if resp.status_code == 401:
                raise ClaudeAuthError("Claude Code auth is no longer valid. Run `claude` again and refresh.")
            resp.raise_for_status()

            metrics = _parse_usage_metrics(resp.json(), now)
            self._log_store.append(category="claude", message="Loaded Claude usage from local Claude Code auth.")

            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.AUTHENTICATED,
                fetch_state=ProviderFetchState.OK,
                fetched_at_utc=now,
                metrics=metrics,
                source_description=self.source_description,
            )

        except ClaudeAuthError as e:
            self._log_store.append(category="claude", message=str(e), level="warning")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.SIGNED_OUT,
                fetch_state=ProviderFetchState.MISSING_AUTH,
                metrics=base_metrics,
                source_description=self.source_description,
            )
        except Exception as e:
            self._log_store.append(category="claude", message=f"Refresh failed: {e}", level="error")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.CONFIGURED,
                fetch_state=ProviderFetchState.FAILED,
                fetched_at_utc=now,
                metrics=base_metrics,
                error_description=str(e),
                source_description=self.source_description,
            )
