from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

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


REFRESH_ENDPOINT = "https://auth.openai.com/oauth/token"
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_BASE_URL = "https://chatgpt.com/backend-api/"


@dataclass
class CodexOAuthCredentials:
    access_token: str
    refresh_token: str = ""
    id_token: Optional[str] = None
    account_id: Optional[str] = None
    last_refresh: Optional[datetime] = None

    @property
    def needs_refresh(self) -> bool:
        if not self.refresh_token:
            return False
        if self.last_refresh is None:
            return True
        return (datetime.now(timezone.utc) - self.last_refresh).total_seconds() > 8 * 86400


class CodexAuthError(Exception):
    pass


def _codex_home() -> Path:
    env_val = os.environ.get("CODEX_HOME", "").strip()
    if env_val:
        return Path(env_val)
    return Path.home() / ".codex"


def _load_credentials() -> CodexOAuthCredentials:
    auth_file = _codex_home() / "auth.json"
    if not auth_file.exists():
        raise CodexAuthError("Codex CLI auth was not found. Run `codex login` and refresh.")
    try:
        data = json.loads(auth_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise CodexAuthError(f"Codex CLI auth could not be read: {e}")
    return _parse_credentials(data)


def _parse_credentials(data: dict) -> CodexOAuthCredentials:
    api_key = _clean(data.get("OPENAI_API_KEY"))
    if api_key:
        return CodexOAuthCredentials(access_token=api_key)

    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        raise CodexAuthError("Codex CLI auth exists but contains no usable tokens. Run `codex login` again.")

    access_token = _clean(tokens.get("access_token")) or _clean(tokens.get("accessToken")) or ""
    if not access_token:
        raise CodexAuthError("Codex CLI auth exists but contains no usable tokens. Run `codex login` again.")

    refresh_token = _clean(tokens.get("refresh_token")) or _clean(tokens.get("refreshToken")) or ""
    id_token = _clean(tokens.get("id_token")) or _clean(tokens.get("idToken"))
    account_id = _clean(tokens.get("account_id")) or _clean(tokens.get("accountId"))
    last_refresh = _parse_iso_date(data.get("last_refresh"))

    return CodexOAuthCredentials(
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
        account_id=account_id,
        last_refresh=last_refresh,
    )


def _save_credentials(creds: CodexOAuthCredentials) -> None:
    auth_file = _codex_home() / "auth.json"
    existing: dict = {}
    if auth_file.exists():
        try:
            existing = json.loads(auth_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    tokens: dict[str, Any] = {
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
    }
    if creds.id_token:
        tokens["id_token"] = creds.id_token
    if creds.account_id:
        tokens["account_id"] = creds.account_id

    existing["tokens"] = tokens
    existing["last_refresh"] = datetime.now(timezone.utc).isoformat()

    auth_file.parent.mkdir(parents=True, exist_ok=True)
    auth_file.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")


def _refresh_token(creds: CodexOAuthCredentials) -> CodexOAuthCredentials:
    if not creds.refresh_token:
        return creds

    resp = requests.post(
        REFRESH_ENDPOINT,
        json={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
            "scope": "openid profile email",
        },
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if resp.status_code == 401:
        error_code = ""
        try:
            body = resp.json()
            error_code = (body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else body.get("error", "")).lower()
        except Exception:
            pass
        if "reused" in error_code:
            raise CodexAuthError("Codex CLI refresh token was already used. Run `codex login` again.")
        if "invalidated" in error_code or "revoked" in error_code:
            raise CodexAuthError("Codex CLI refresh token was revoked. Run `codex login` again.")
        raise CodexAuthError("Codex CLI refresh token expired. Run `codex login` again.")

    if resp.status_code != 200:
        raise CodexAuthError(f"Codex auth refresh failed: Status {resp.status_code}")

    body = resp.json()
    return CodexOAuthCredentials(
        access_token=body.get("access_token", creds.access_token),
        refresh_token=body.get("refresh_token", creds.refresh_token),
        id_token=body.get("id_token", creds.id_token),
        account_id=creds.account_id,
        last_refresh=datetime.now(timezone.utc),
    )


def _chatgpt_base_url() -> str:
    config_file = _codex_home() / "config.toml"
    if not config_file.exists():
        return DEFAULT_BASE_URL

    try:
        contents = config_file.read_text(encoding="utf-8")
    except Exception:
        return DEFAULT_BASE_URL

    for raw_line in contents.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split("=", 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        if key != "chatgpt_base_url":
            continue
        value = parts[1].strip().strip("\"'")
        return _normalize_base_url(value)

    return DEFAULT_BASE_URL


def _normalize_base_url(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        trimmed = "https://chatgpt.com/backend-api"
    trimmed = trimmed.rstrip("/")
    if (trimmed.startswith("https://chatgpt.com") or trimmed.startswith("https://chat.openai.com")) and "/backend-api" not in trimmed:
        trimmed += "/backend-api"
    return trimmed + "/"


def _resolve_usage_url(base_url: str) -> str:
    if "/backend-api/" in base_url:
        return base_url.rstrip("/") + "/wham/usage"
    return base_url.rstrip("/") + "/api/codex/usage"


def _parse_api_metric(window: dict, kind: UsageMetricKind, now: datetime) -> Optional[UsageMetric]:
    used_percent = _number(window.get("used_percent"))
    if used_percent is None:
        return None

    remaining_fraction = max(0.0, min(1.0, 1.0 - (used_percent / 100.0)))
    reset_at_raw = _number(window.get("reset_at"))
    reset_at = datetime.fromtimestamp(reset_at_raw, tz=timezone.utc) if reset_at_raw else None

    return UsageMetric(
        kind=kind,
        remaining_fraction=remaining_fraction,
        remaining_value=remaining_fraction * 100,
        total_value=100.0,
        unit=MetricUnit.PERCENTAGE,
        reset_at_utc=reset_at,
        last_updated_at_utc=now,
        detail_text=f"{int(round(remaining_fraction * 100))}% remaining",
    )


def _is_codex_spark_limit(item: dict) -> bool:
    return item.get("limit_name") == "GPT-5.3-Codex-Spark" or item.get("metered_feature") == "codex_bengalfox"


def _parse_usage_payload(payload: dict, now: datetime) -> list[UsageMetric]:
    metrics: list[UsageMetric] = []

    rate_limit = payload.get("rate_limit")
    if isinstance(rate_limit, dict):
        pw = rate_limit.get("primary_window")
        if isinstance(pw, dict):
            m = _parse_api_metric(pw, UsageMetricKind.CODEX_FIVE_HOUR, now)
            if m:
                metrics.append(m)
        sw = rate_limit.get("secondary_window")
        if isinstance(sw, dict):
            m = _parse_api_metric(sw, UsageMetricKind.CODEX_WEEKLY, now)
            if m:
                metrics.append(m)

    additional = payload.get("additional_rate_limits")
    if isinstance(additional, list):
        spark = next((x for x in additional if isinstance(x, dict) and _is_codex_spark_limit(x)), None)
        if spark and isinstance(spark.get("rate_limit"), dict):
            srl = spark["rate_limit"]
            pw = srl.get("primary_window")
            if isinstance(pw, dict):
                m = _parse_api_metric(pw, UsageMetricKind.CODEX_SPARK_FIVE_HOUR, now)
                if m:
                    metrics.append(m)
            sw = srl.get("secondary_window")
            if isinstance(sw, dict):
                m = _parse_api_metric(sw, UsageMetricKind.CODEX_SPARK_WEEKLY, now)
                if m:
                    metrics.append(m)

    credits_data = payload.get("credits")
    if isinstance(credits_data, dict):
        balance = _number(credits_data.get("balance"))
        if balance is not None:
            metrics.append(UsageMetric(
                kind=UsageMetricKind.CODEX_CREDITS,
                remaining_value=balance,
                unit=MetricUnit.CREDITS,
                last_updated_at_utc=now,
                detail_text=f"{int(round(balance))} credits",
            ))

    if not metrics:
        raise CodexAuthError("The Codex usage API did not expose recognizable usage or credit metrics.")

    present_kinds = {m.kind for m in metrics}
    all_codex_kinds = [
        UsageMetricKind.CODEX_FIVE_HOUR, UsageMetricKind.CODEX_WEEKLY,
        UsageMetricKind.CODEX_SPARK_FIVE_HOUR, UsageMetricKind.CODEX_SPARK_WEEKLY,
        UsageMetricKind.CODEX_CREDITS,
    ]
    for kind in all_codex_kinds:
        if kind not in present_kinds:
            metrics.append(UsageMetric(
                kind=kind,
                unit=MetricUnit.CREDITS if kind == UsageMetricKind.CODEX_CREDITS else MetricUnit.PERCENTAGE,
                last_updated_at_utc=now,
            ))

    order = {k: i for i, k in enumerate(all_codex_kinds)}
    metrics.sort(key=lambda m: order.get(m.kind, 99))
    return metrics


def _clean(value: Any) -> Optional[str]:
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return None


def _number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _parse_iso_date(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc) if "Z" in fmt else datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class CodexProvider:
    id = ProviderID.CODEX
    source_description = "Local Codex CLI auth"

    def __init__(self, log_store: LogStore):
        self._log_store = log_store

    def current_auth_state(self) -> ProviderAuthState:
        try:
            _load_credentials()
            return ProviderAuthState.CONFIGURED
        except CodexAuthError:
            return ProviderAuthState.SIGNED_OUT

    def clear_auth(self) -> None:
        pass

    def refresh(self, now: datetime) -> ProviderSnapshot:
        base_metrics = [
            UsageMetric(kind=UsageMetricKind.CODEX_FIVE_HOUR, last_updated_at_utc=now),
            UsageMetric(kind=UsageMetricKind.CODEX_WEEKLY, last_updated_at_utc=now),
            UsageMetric(kind=UsageMetricKind.CODEX_SPARK_FIVE_HOUR, last_updated_at_utc=now),
            UsageMetric(kind=UsageMetricKind.CODEX_SPARK_WEEKLY, last_updated_at_utc=now),
            UsageMetric(kind=UsageMetricKind.CODEX_CREDITS, unit=MetricUnit.CREDITS, last_updated_at_utc=now),
        ]

        try:
            creds = _load_credentials()
            if creds.needs_refresh:
                creds = _refresh_token(creds)
                _save_credentials(creds)
                self._log_store.append(category="codex", message="Refreshed local Codex CLI auth token.")

            base_url = _chatgpt_base_url()
            usage_url = _resolve_usage_url(base_url)

            headers = {
                "Authorization": f"Bearer {creds.access_token}",
                "Accept": "application/json",
                "User-Agent": "AI Usage",
            }
            if creds.account_id:
                headers["ChatGPT-Account-Id"] = creds.account_id

            resp = requests.get(usage_url, headers=headers, timeout=30)
            self._log_store.append(category="codex", message=f"HTTP {resp.status_code} for {usage_url}")

            if resp.status_code in (401, 403):
                raise CodexAuthError("Codex CLI auth is no longer valid. Run `codex login` and refresh.")
            resp.raise_for_status()

            payload = resp.json()
            metrics = _parse_usage_payload(payload, now)
            self._log_store.append(category="codex", message="Loaded Codex usage from local CLI auth.")

            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.AUTHENTICATED,
                fetch_state=ProviderFetchState.OK,
                fetched_at_utc=now,
                metrics=metrics,
                source_description=self.source_description,
            )

        except CodexAuthError as e:
            self._log_store.append(category="codex", message=str(e), level="warning")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.SIGNED_OUT,
                fetch_state=ProviderFetchState.MISSING_AUTH,
                metrics=base_metrics,
                source_description=self.source_description,
            )
        except Exception as e:
            self._log_store.append(category="codex", message=f"Refresh failed: {e}", level="error")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.CONFIGURED,
                fetch_state=ProviderFetchState.FAILED,
                fetched_at_utc=now,
                metrics=base_metrics,
                error_description=str(e),
                source_description=self.source_description,
            )
