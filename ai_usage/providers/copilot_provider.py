from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

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
from ai_usage.services.secret_store import SecretStore

USAGE_URL = "https://api.github.com/copilot_internal/user"
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
CLIENT_ID = "Iv1.b507a08c87ecfe98"
SCOPES = "read:user"
TOKEN_ACCOUNT = "copilot.github-oauth-token"


def _next_reset(now: datetime) -> datetime:
    if now.month == 12:
        return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _find_number(payload: Any, candidate_keys: list[str]) -> float | None:
    if isinstance(payload, dict):
        for key in candidate_keys:
            raw = payload.get(key)
            if raw is not None:
                n = _number(raw)
                if n is not None:
                    return n
        for v in payload.values():
            result = _find_number(v, candidate_keys)
            if result is not None:
                return result
    if isinstance(payload, list):
        for item in payload:
            result = _find_number(item, candidate_keys)
            if result is not None:
                return result
    return None


def _normalized_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _quota_snapshot(payload: Any, quota_id_fallback: str | None = None) -> dict | None:
    if not isinstance(payload, dict):
        return None
    entitlement = _number(payload.get("entitlement"))
    remaining = _number(payload.get("remaining"))
    percent_remaining = _number(payload.get("percent_remaining"))
    if percent_remaining is None and entitlement and remaining and entitlement > 0:
        percent_remaining = (remaining / entitlement) * 100

    return {
        "entitlement": entitlement,
        "remaining": remaining,
        "percent_remaining": percent_remaining,
        "is_usable": remaining is not None and percent_remaining is not None,
    }


def _parse_reset_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _gather_usage_items(payload: dict) -> list[dict]:
    results = []
    items = payload.get("usageItems")
    if isinstance(items, list):
        results.extend(items)
    for v in payload.values():
        if isinstance(v, dict):
            results.extend(_gather_usage_items(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    results.extend(_gather_usage_items(item))
    return results


def _parse_from_internal(payload: dict, now: datetime) -> UsageMetric | None:
    quota_snapshots = payload.get("quota_snapshots") or payload.get("quotaSnapshots") or {}
    if not isinstance(quota_snapshots, dict):
        return None

    premium = _quota_snapshot(quota_snapshots.get("premium_interactions"), "premium_interactions")
    chat = _quota_snapshot(quota_snapshots.get("chat"), "chat")

    monthly_quotas = payload.get("monthly_quotas") or payload.get("monthlyQuotas") or {}
    limited_quotas = payload.get("limited_user_quotas") or payload.get("limitedUserQuotas") or {}

    def _monthly_snapshot(entitlement_val, remaining_val):
        e = _number(entitlement_val)
        r = _number(remaining_val)
        if e and r and e > 0:
            return {"entitlement": e, "remaining": r, "percent_remaining": (r / e) * 100, "is_usable": True}
        return None

    fb_premium = _monthly_snapshot(
        monthly_quotas.get("completions") or monthly_quotas.get("premium_interactions"),
        limited_quotas.get("completions") or limited_quotas.get("premium_interactions"),
    )
    fb_chat = _monthly_snapshot(monthly_quotas.get("chat"), limited_quotas.get("chat"))

    unknown = None
    for v in quota_snapshots.values():
        qs = _quota_snapshot(v)
        if qs and qs["is_usable"]:
            unknown = qs
            break

    selected = None
    for candidate in [premium, fb_premium, chat, fb_chat, unknown]:
        if candidate and candidate.get("is_usable"):
            selected = candidate
            break

    if selected is None or selected.get("remaining") is None:
        return None

    remaining = selected["remaining"]
    total = selected.get("entitlement")
    fraction = max(0.0, min(1.0, selected["percent_remaining"] / 100)) if selected.get("percent_remaining") is not None else None
    reset_at = _parse_reset_date(payload.get("quota_reset_date") or payload.get("quotaResetDate")) or _next_reset(now)

    if total:
        detail = f"{int(round(remaining))} of {int(round(total))} requests left"
    else:
        detail = f"{int(round(remaining))} requests left"

    return UsageMetric(
        kind=UsageMetricKind.COPILOT_MONTHLY,
        remaining_fraction=fraction,
        remaining_value=remaining,
        total_value=total,
        unit=MetricUnit.REQUESTS,
        reset_at_utc=reset_at,
        last_updated_at_utc=now,
        detail_text=detail,
    )


def _parse_from_billing_session(payload: dict, now: datetime) -> UsageMetric | None:
    total = _find_number(payload, ["userPremiumRequestEntitlement", "filteredUserPremiumRequestEntitlement"]) or 0
    used = _find_number(payload, ["discountQuantity", "discount_quantity"]) or 0
    if total <= 0:
        return None
    remaining = max(total - used, 0)
    fraction = max(0.0, min(1.0, remaining / total))
    return UsageMetric(
        kind=UsageMetricKind.COPILOT_MONTHLY,
        remaining_fraction=fraction,
        remaining_value=remaining,
        total_value=total,
        unit=MetricUnit.REQUESTS,
        reset_at_utc=_next_reset(now),
        last_updated_at_utc=now,
        detail_text=f"{int(round(remaining))} of {int(round(total))} requests left",
    )


def _parse_from_usage_report(payload: dict, now: datetime) -> UsageMetric | None:
    usage_items_raw = payload.get("usageItems")
    if isinstance(usage_items_raw, list) and not usage_items_raw:
        return UsageMetric(
            kind=UsageMetricKind.COPILOT_MONTHLY,
            unit=MetricUnit.REQUESTS,
            reset_at_utc=_next_reset(now),
            last_updated_at_utc=now,
            detail_text="0 requests used this month",
        )

    items = _gather_usage_items(payload)
    if not items:
        return None

    copilot_items = [
        item for item in items
        if "copilot" in _normalized_string(item.get("product")).lower()
        or "premium request" in _normalized_string(item.get("sku")).lower()
        or "copilot" in _normalized_string(item.get("sku")).lower()
    ]
    if not copilot_items:
        return None

    total_keys = ["total_monthly_quota", "monthly_quota", "included_usage", "includedUsage", "quota", "total_quota", "included_quota", "includedQuota", "included_quantity", "includedQuantity"]
    total_quota = _find_number(payload, total_keys)
    if total_quota is None:
        values = [_find_number(item, total_keys) for item in copilot_items]
        values = [v for v in values if v is not None]
        total_quota = max(values) if values else None

    used_keys = ["netQuantity", "grossQuantity", "quantity", "used_quota", "usedQuota", "used_quantity", "usedQuantity", "consumed_usage", "consumedUsage"]
    used_value = sum(_find_number(item, used_keys) or 0 for item in copilot_items)

    remaining_value = max(total_quota - used_value, 0) if total_quota else None
    fraction = max(0.0, min(1.0, remaining_value / max(total_quota, 1))) if total_quota and remaining_value is not None else None

    if total_quota and remaining_value is not None:
        detail = f"{int(round(remaining_value))} of {int(round(total_quota))} requests left"
    else:
        detail = f"{int(round(used_value))} requests used this month"

    return UsageMetric(
        kind=UsageMetricKind.COPILOT_MONTHLY,
        remaining_fraction=fraction,
        remaining_value=remaining_value,
        total_value=total_quota,
        unit=MetricUnit.REQUESTS,
        reset_at_utc=_next_reset(now),
        last_updated_at_utc=now,
        detail_text=detail,
    )


def _parse_metric(payload: Any, now: datetime) -> UsageMetric:
    if isinstance(payload, dict):
        result = _parse_from_internal(payload, now)
        if result:
            return result
        result = _parse_from_billing_session(payload, now)
        if result:
            return result
        result = _parse_from_usage_report(payload, now)
        if result:
            return result

    remaining = _find_number(payload, ["remaining_quota", "remainingQuota", "remaining_requests", "remainingRequests", "quota_remaining", "remaining_included_usage", "remainingIncludedUsage", "remaining_included_quota", "remainingIncludedQuota", "remaining_included_quantity", "remainingIncludedQuantity"])
    total = _find_number(payload, ["total_monthly_quota", "monthly_quota", "included_usage", "includedUsage", "quota", "total_quota", "included_quota", "includedQuota", "included_quantity", "includedQuantity", "userPremiumRequestEntitlement", "filteredUserPremiumRequestEntitlement"])
    used = _find_number(payload, ["discountQuantity", "discount_quantity", "used_quota", "usedQuota", "consumed_usage", "consumedUsage", "usage", "used", "used_quantity", "usedQuantity", "included_usage_consumed", "includedUsageConsumed", "netQuantity", "grossQuantity", "quantity"])

    resolved_remaining = remaining
    if resolved_remaining is None and total is not None and used is not None:
        resolved_remaining = max(total - used, 0)

    resolved_total = total
    if resolved_total is None and resolved_remaining is not None and used is not None:
        resolved_total = resolved_remaining + used

    if resolved_remaining is None:
        raise Exception("GitHub Copilot usage response wasn't recognized.")

    fraction = max(0.0, min(1.0, resolved_remaining / max(resolved_total, 1))) if resolved_total else None
    if resolved_total:
        detail = f"{int(round(resolved_remaining))} of {int(round(resolved_total))} requests left"
    else:
        detail = f"{int(round(resolved_remaining))} requests left"

    return UsageMetric(
        kind=UsageMetricKind.COPILOT_MONTHLY,
        remaining_fraction=fraction,
        remaining_value=resolved_remaining,
        total_value=resolved_total,
        unit=MetricUnit.REQUESTS,
        reset_at_utc=_next_reset(now),
        last_updated_at_utc=now,
        detail_text=detail,
    )


class CopilotDeviceFlow:
    @staticmethod
    def request_device_code() -> dict:
        resp = requests.post(
            DEVICE_CODE_URL,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode({"client_id": CLIENT_ID, "scope": SCOPES}),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def poll_for_token(device_code: str, interval: int) -> str:
        while True:
            time.sleep(interval)
            resp = requests.post(
                ACCESS_TOKEN_URL,
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                data=urlencode({
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                }),
                timeout=30,
            )
            body = resp.json()
            error = body.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                time.sleep(5)
                continue
            if error == "expired_token":
                raise Exception("GitHub sign-in expired before it was completed.")
            if error:
                raise Exception(f"GitHub sign-in failed: {error}")
            token = body.get("access_token")
            if token:
                return token
            raise Exception("GitHub sign-in returned an unexpected response.")


class CopilotProvider:
    id = ProviderID.COPILOT
    source_description = "GitHub device-flow token"

    def __init__(self, secret_store: SecretStore, log_store: LogStore):
        self._secret_store = secret_store
        self._log_store = log_store

    def current_auth_state(self) -> ProviderAuthState:
        token = self._secret_store.load(TOKEN_ACCOUNT)
        return ProviderAuthState.CONFIGURED if token else ProviderAuthState.SIGNED_OUT

    def save_token(self, token: str) -> None:
        self._secret_store.save(TOKEN_ACCOUNT, token.strip())

    def clear_auth(self) -> None:
        self._secret_store.delete(TOKEN_ACCOUNT)

    def refresh(self, now: datetime) -> ProviderSnapshot:
        base_metric = UsageMetric(
            kind=UsageMetricKind.COPILOT_MONTHLY,
            unit=MetricUnit.REQUESTS,
            reset_at_utc=_next_reset(now),
            last_updated_at_utc=now,
        )

        token = self._secret_store.load(TOKEN_ACCOUNT)
        if not token:
            self._log_store.append(category="copilot", message="Refresh skipped: no GitHub OAuth token configured.", level="warning")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.SIGNED_OUT,
                fetch_state=ProviderFetchState.MISSING_AUTH,
                metrics=[base_metric],
                source_description=self.source_description,
            )

        try:
            resp = requests.get(
                USAGE_URL,
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/json",
                    "Editor-Version": "vscode/1.96.2",
                    "Editor-Plugin-Version": "copilot-chat/0.26.7",
                    "User-Agent": "GitHubCopilotChat/0.26.7",
                    "X-Github-Api-Version": "2025-04-01",
                },
                timeout=30,
            )
            self._log_store.append(category="copilot", message=f"HTTP {resp.status_code} for {USAGE_URL}")

            if resp.status_code in (401, 403):
                raise Exception("GitHub Copilot sign-in expired. Sign in again and refresh.")
            resp.raise_for_status()

            payload = resp.json()
            metric = _parse_metric(payload, now)
            self._log_store.append(category="copilot", message="Parsed GitHub Copilot usage from internal API.")

            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.AUTHENTICATED,
                fetch_state=ProviderFetchState.OK,
                fetched_at_utc=now,
                metrics=[metric],
                source_description=self.source_description,
            )
        except Exception as e:
            self._log_store.append(category="copilot", message=f"Refresh failed: {e}", level="error")
            return ProviderSnapshot(
                provider=self.id,
                auth_state=ProviderAuthState.CONFIGURED,
                fetch_state=ProviderFetchState.FAILED,
                fetched_at_utc=now,
                metrics=[base_metric],
                error_description=str(e),
                source_description=self.source_description,
            )
