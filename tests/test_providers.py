from datetime import datetime, timezone

from ai_usage.domain.models import UsageMetricKind
from ai_usage.providers.claude_provider import _parse_usage_metrics
from ai_usage.providers.codex_provider import _parse_usage_payload

NOW = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)


def _by_kind(metrics):
    return {m.kind: m for m in metrics}


def test_claude_utilization_is_a_percentage():
    # API reports utilization as 0..100, not 0..1.
    data = {
        "five_hour": {"utilization": 4.0, "resets_at": "2026-09-07T16:10:00+00:00"},
        "seven_day": {"utilization": 17.0, "resets_at": "2026-09-08T22:00:00+00:00"},
    }
    metrics = _by_kind(_parse_usage_metrics(data, NOW))

    assert metrics[UsageMetricKind.CLAUDE_FIVE_HOUR].remaining_fraction == 0.96
    assert metrics[UsageMetricKind.CLAUDE_WEEKLY].remaining_fraction == 0.83


def test_claude_missing_window_has_no_fraction():
    metrics = _by_kind(_parse_usage_metrics({}, NOW))
    assert metrics[UsageMetricKind.CLAUDE_WEEKLY].remaining_fraction is None


def test_codex_classifies_windows_by_duration_not_position():
    # Plan exposes only a weekly window, delivered as `primary_window`.
    payload = {
        "rate_limit": {
            "primary_window": {
                "used_percent": 28,
                "limit_window_seconds": 604800,
                "reset_at": 1789309516,
            },
            "secondary_window": None,
        },
        "credits": {"has_credits": False, "balance": "0"},
    }
    metrics = _by_kind(_parse_usage_payload(payload, NOW))

    assert metrics[UsageMetricKind.CODEX_WEEKLY].remaining_fraction == 0.72
    assert metrics[UsageMetricKind.CODEX_FIVE_HOUR].remaining_fraction is None


def test_codex_five_hour_window_is_recognized():
    payload = {
        "rate_limit": {
            "primary_window": {"used_percent": 10, "limit_window_seconds": 18000},
            "secondary_window": {"used_percent": 40, "limit_window_seconds": 604800},
        }
    }
    metrics = _by_kind(_parse_usage_payload(payload, NOW))

    assert metrics[UsageMetricKind.CODEX_FIVE_HOUR].remaining_fraction == 0.9
    assert metrics[UsageMetricKind.CODEX_WEEKLY].remaining_fraction == 0.6
