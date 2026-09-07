from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ai_usage.domain.models import (
    UsageAlertDirection,
    UsageAlertState,
    UsageMetric,
    UsageMetricKind,
)


class UsagePaceState:
    AHEAD = "ahead"
    ON_TRACK = "onTrack"
    BEHIND = "behind"


@dataclass
class UsagePaceAssessment:
    state: str
    expected_remaining: float
    actual_remaining: float
    delta: float


@dataclass
class EvaluatorResult:
    direction: UsageAlertDirection
    state: UsageAlertState
    should_notify: bool
    delta: float
    expected_remaining: float
    actual_remaining: float


def _period_range(metric: UsageMetric, now: datetime) -> tuple[datetime, datetime, float] | None:
    reset = metric.reset_at_utc
    if reset is None:
        return None

    kind = metric.kind
    if kind in {UsageMetricKind.CODEX_FIVE_HOUR, UsageMetricKind.CODEX_SPARK_FIVE_HOUR, UsageMetricKind.CLAUDE_FIVE_HOUR}:
        duration = 5 * 3600.0
        start = reset - timedelta(seconds=duration)
        return (start, reset, duration)

    if kind in {UsageMetricKind.CODEX_WEEKLY, UsageMetricKind.CODEX_SPARK_WEEKLY, UsageMetricKind.CLAUDE_WEEKLY}:
        duration = 7 * 24 * 3600.0
        start = reset - timedelta(seconds=duration)
        return (start, reset, duration)

    if kind == UsageMetricKind.COPILOT_MONTHLY:
        if reset.month == 1:
            prev_year, prev_month = reset.year - 1, 12
        else:
            prev_year, prev_month = reset.year, reset.month - 1
        start = reset.replace(year=prev_year, month=prev_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        duration = max((reset - start).total_seconds(), 1.0)
        return (start, reset, duration)

    return None


def _same_reset(a: datetime | None, b: datetime | None) -> bool:
    """Treat two reset timestamps as the same window.

    The upstream APIs return a ``resets_at`` value that jitters by fractions of
    a second (sometimes a few minutes) on every poll, so an exact comparison
    would make the alert state look like a brand-new window each refresh and
    re-fire the notification. A genuine early reset moves the timestamp by far
    more than this tolerance.
    """
    if a is None or b is None:
        return a is b
    return abs((a - b).total_seconds()) <= 5 * 60


class ScheduleEvaluator:
    TRIGGER = 0.18
    REARM_MARGIN = 0.10

    def pace_assessment(
        self, metric: UsageMetric, now: datetime, trigger: float = 0.09
    ) -> UsagePaceAssessment | None:
        if metric.remaining_fraction is None:
            return None
        period = _period_range(metric, now)
        if period is None:
            return None

        start, end, duration = period
        elapsed = max(0.0, min(1.0, (now - start).total_seconds() / duration))
        expected_remaining = 1.0 - elapsed
        actual_remaining = metric.remaining_fraction
        delta = actual_remaining - expected_remaining

        if delta <= -trigger:
            state = UsagePaceState.AHEAD
        elif delta >= trigger:
            state = UsagePaceState.BEHIND
        else:
            state = UsagePaceState.ON_TRACK

        return UsagePaceAssessment(
            state=state,
            expected_remaining=expected_remaining,
            actual_remaining=actual_remaining,
            delta=delta,
        )

    def evaluate(
        self,
        metric: UsageMetric,
        direction: UsageAlertDirection,
        previous_state: UsageAlertState | None,
        now: datetime,
    ) -> EvaluatorResult | None:
        assessment = self.pace_assessment(metric, now, trigger=self.TRIGGER)
        if assessment is None:
            return None

        actual_remaining = assessment.actual_remaining
        expected_remaining = assessment.expected_remaining
        delta = assessment.delta

        if direction == UsageAlertDirection.AHEAD:
            severity = -delta
            if not metric.kind.supports_ahead_notifications:
                return None
        else:
            severity = delta
            if not metric.kind.supports_behind_notifications:
                return None

        if severity <= 0:
            state = UsageAlertState(
                direction=direction,
                metric_kind=metric.kind,
                last_triggered_at_utc=previous_state.last_triggered_at_utc if previous_state else now,
                last_extreme_delta=0.0,
                last_reset_at_utc=metric.reset_at_utc,
                is_armed=True,
            )
            return EvaluatorResult(direction=direction, state=state, should_notify=False, delta=delta, expected_remaining=expected_remaining, actual_remaining=actual_remaining)

        should_reset = (
            previous_state is None
            or not _same_reset(previous_state.last_reset_at_utc, metric.reset_at_utc)
            or previous_state.direction != direction
            or previous_state.metric_kind != metric.kind
        )

        if should_reset or previous_state is None:
            state = UsageAlertState(
                direction=direction,
                metric_kind=metric.kind,
                last_triggered_at_utc=now,
                last_extreme_delta=0.0,
                last_reset_at_utc=metric.reset_at_utc,
                is_armed=True,
            )
        else:
            state = UsageAlertState(
                direction=previous_state.direction,
                metric_kind=previous_state.metric_kind,
                last_triggered_at_utc=previous_state.last_triggered_at_utc,
                last_extreme_delta=previous_state.last_extreme_delta,
                last_reset_at_utc=previous_state.last_reset_at_utc,
                is_armed=previous_state.is_armed,
            )

        rearm_threshold = max(0.0, self.TRIGGER - self.REARM_MARGIN)

        if severity <= rearm_threshold:
            state.is_armed = True
            state.last_extreme_delta = severity
            state.last_reset_at_utc = metric.reset_at_utc
            return EvaluatorResult(direction=direction, state=state, should_notify=False, delta=delta, expected_remaining=expected_remaining, actual_remaining=actual_remaining)

        if severity >= self.TRIGGER and state.is_armed:
            state.is_armed = False
            state.last_triggered_at_utc = now
            state.last_extreme_delta = severity
            state.last_reset_at_utc = metric.reset_at_utc
            return EvaluatorResult(direction=direction, state=state, should_notify=True, delta=delta, expected_remaining=expected_remaining, actual_remaining=actual_remaining)

        state.last_extreme_delta = max(state.last_extreme_delta, severity)
        state.last_reset_at_utc = metric.reset_at_utc
        return EvaluatorResult(direction=direction, state=state, should_notify=False, delta=delta, expected_remaining=expected_remaining, actual_remaining=actual_remaining)
