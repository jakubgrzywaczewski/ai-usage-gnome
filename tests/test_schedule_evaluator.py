from datetime import datetime, timedelta, timezone

from ai_usage.domain.models import UsageAlertDirection, UsageMetric, UsageMetricKind
from ai_usage.domain.schedule_evaluator import ScheduleEvaluator, _same_reset

NOW = datetime(2026, 9, 7, 13, 50, tzinfo=timezone.utc)


def _weekly_metric(remaining: float, reset_microsecond: int = 0) -> UsageMetric:
    # Window is one week; reset ~1.3 days out => most of the week has elapsed.
    return UsageMetric(
        kind=UsageMetricKind.CLAUDE_WEEKLY,
        remaining_fraction=remaining,
        reset_at_utc=datetime(2026, 9, 8, 22, 0, 0, reset_microsecond, tzinfo=timezone.utc),
        last_updated_at_utc=NOW,
    )


def test_same_reset_tolerates_sub_second_jitter():
    a = datetime(2026, 9, 8, 22, 0, 0, 227487, tzinfo=timezone.utc)
    b = datetime(2026, 9, 8, 22, 0, 0, 97291, tzinfo=timezone.utc)
    assert _same_reset(a, b)


def test_same_reset_detects_a_real_early_reset():
    a = datetime(2026, 9, 8, 22, 0, tzinfo=timezone.utc)
    b = datetime(2026, 9, 8, 20, 0, tzinfo=timezone.utc)
    assert not _same_reset(a, b)


def test_behind_notification_fires_once_despite_reset_jitter():
    ev = ScheduleEvaluator()
    state = None
    notifications = 0
    for i in range(6):
        metric = _weekly_metric(0.83, reset_microsecond=200000 + i * 37000)
        result = ev.evaluate(
            metric, UsageAlertDirection.BEHIND, state, NOW + timedelta(minutes=5 * i)
        )
        assert result is not None
        state = result.state
        notifications += int(result.should_notify)
    assert notifications == 1


def test_new_window_rearms_the_alert():
    ev = ScheduleEvaluator()
    first = ev.evaluate(_weekly_metric(0.83), UsageAlertDirection.BEHIND, None, NOW)
    assert first.should_notify

    # A genuinely different reset date -> treated as a fresh window.
    next_window = UsageMetric(
        kind=UsageMetricKind.CLAUDE_WEEKLY,
        remaining_fraction=0.83,
        reset_at_utc=datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc),
        last_updated_at_utc=NOW,
    )
    second = ev.evaluate(
        next_window, UsageAlertDirection.BEHIND, first.state, NOW + timedelta(days=7)
    )
    assert second.should_notify
