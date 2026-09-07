from __future__ import annotations

import logging
from datetime import datetime

from ai_usage.domain.localization import L10nKey, Localizer
from ai_usage.domain.models import (
    DisplayPreferences,
    ProviderID,
    ProviderSnapshot,
    UsageAlertDirection,
    UsageMetricKind,
)
from ai_usage.domain.schedule_evaluator import ScheduleEvaluator
from ai_usage.services.usage_store import UsageStore

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify as _Notify
    _HAS_NOTIFY = True
except (ImportError, ValueError):
    _HAS_NOTIFY = False


class NotificationService:
    def __init__(self, usage_store: UsageStore):
        self._usage_store = usage_store
        self._evaluator = ScheduleEvaluator()
        self._initialized = False
        if _HAS_NOTIFY:
            try:
                _Notify.init("AI Usage")
                self._initialized = True
            except Exception as e:
                logger.warning("Could not initialize libnotify: %s", e)

    @property
    def notifications_available(self) -> bool:
        return _HAS_NOTIFY and self._initialized

    def _send(self, title: str, body: str) -> None:
        if not self._initialized:
            return
        try:
            n = _Notify.Notification.new(title, body, "dialog-information")
            n.show()
        except Exception as e:
            logger.warning("Failed to send notification: %s", e)

    def process_refresh(
        self,
        previous_snapshots: dict[ProviderID, ProviderSnapshot],
        new_snapshots: dict[ProviderID, ProviderSnapshot],
        preferences: DisplayPreferences,
        now: datetime,
    ) -> None:
        localizer = Localizer(preferences.language)
        alert_states = self._usage_store.load_alert_states()
        reset_markers = self._usage_store.load_reset_markers()

        for snapshot in new_snapshots.values():
            if snapshot.fetch_state.value != "ok":
                continue
            for metric in snapshot.metrics:
                alert_key_ahead = f"{metric.kind.value}-{UsageAlertDirection.AHEAD.value}"
                alert_key_behind = f"{metric.kind.value}-{UsageAlertDirection.BEHIND.value}"

                if preferences.show_ahead_notifications:
                    result = self._evaluator.evaluate(
                        metric=metric,
                        direction=UsageAlertDirection.AHEAD,
                        previous_state=alert_states.get(alert_key_ahead),
                        now=now,
                    )
                    if result:
                        alert_states[alert_key_ahead] = result.state
                        if result.should_notify:
                            self._send(
                                self._title(metric.kind, UsageAlertDirection.AHEAD, localizer),
                                self._body(result.actual_remaining, result.expected_remaining, localizer),
                            )

                if preferences.show_behind_notifications:
                    result = self._evaluator.evaluate(
                        metric=metric,
                        direction=UsageAlertDirection.BEHIND,
                        previous_state=alert_states.get(alert_key_behind),
                        now=now,
                    )
                    if result:
                        alert_states[alert_key_behind] = result.state
                        if result.should_notify:
                            self._send(
                                self._title(metric.kind, UsageAlertDirection.BEHIND, localizer),
                                self._body(result.actual_remaining, result.expected_remaining, localizer),
                            )

        if preferences.show_codex_reset_notifications:
            self._process_early_reset(
                previous_snapshots, new_snapshots,
                [UsageMetricKind.CODEX_FIVE_HOUR, UsageMetricKind.CODEX_WEEKLY],
                localizer.text(L10nKey.NOTIFICATION_TITLE_CODEX_RESET),
                reset_markers, localizer, now,
            )

        if preferences.show_claude_reset_notifications:
            self._process_early_reset(
                previous_snapshots, new_snapshots,
                [UsageMetricKind.CLAUDE_FIVE_HOUR, UsageMetricKind.CLAUDE_WEEKLY],
                localizer.text(L10nKey.NOTIFICATION_TITLE_CLAUDE_RESET),
                reset_markers, localizer, now,
            )

        self._usage_store.save_alert_states(alert_states)
        self._usage_store.save_reset_markers(reset_markers)

    def _process_early_reset(
        self,
        previous_snapshots: dict[ProviderID, ProviderSnapshot],
        new_snapshots: dict[ProviderID, ProviderSnapshot],
        metric_kinds: list[UsageMetricKind],
        title: str,
        reset_markers: set[str],
        localizer: Localizer,
        now: datetime,
    ) -> None:
        from datetime import timedelta

        for kind in metric_kinds:
            prev_snap = previous_snapshots.get(kind.provider)
            new_snap = new_snapshots.get(kind.provider)
            if not prev_snap or not new_snap:
                continue
            previous = prev_snap.metric(kind)
            current = new_snap.metric(kind)
            if not previous or not current:
                continue
            prev_reset = previous.reset_at_utc
            curr_reset = current.reset_at_utc
            if not prev_reset or not curr_reset:
                continue

            marker = f"{kind.value}-{curr_reset.isoformat()}"
            remaining_jump = (current.remaining_fraction or 0) - (previous.remaining_fraction or 0)
            reset_moved_forward = (curr_reset - prev_reset).total_seconds() > 15 * 60
            happened_early = now < prev_reset - timedelta(minutes=5)

            if happened_early and reset_moved_forward and remaining_jump > 0.25 and marker not in reset_markers:
                reset_markers.add(marker)
                human = localizer.notification_metric_name(kind)
                self._send(title, localizer.formatted(L10nKey.NOTIFICATION_BODY_RESET_FORMAT, human))

    def _title(self, kind: UsageMetricKind, direction: UsageAlertDirection, localizer: Localizer) -> str:
        key = L10nKey.NOTIFICATION_TITLE_AHEAD_FORMAT if direction == UsageAlertDirection.AHEAD else L10nKey.NOTIFICATION_TITLE_BEHIND_FORMAT
        human = localizer.notification_metric_name(kind)
        return localizer.formatted(key, human)

    def _body(self, actual: float, expected: float, localizer: Localizer) -> str:
        return localizer.formatted(L10nKey.NOTIFICATION_BODY_SCHEDULE_FORMAT, int(round(actual * 100)), int(round(expected * 100)))
