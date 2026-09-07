from __future__ import annotations

import threading
from datetime import datetime, timezone

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib

from ai_usage.domain.localization import Localizer
from ai_usage.domain.models import (
    DisplayPreferences,
    MenuBarSummaryItem,
    MetricUnit,
    ProviderAuthState,
    ProviderFetchState,
    ProviderID,
    ProviderSnapshot,
    UsageMetric,
    UsageMetricKind,
)
from ai_usage.providers.claude_provider import ClaudeProvider
from ai_usage.providers.codex_provider import CodexProvider
from ai_usage.providers.copilot_provider import CopilotProvider
from ai_usage.services.log_store import LogStore
from ai_usage.services.notification_service import NotificationService
from ai_usage.services.secret_store import SecretStore
from ai_usage.services.settings_store import SettingsStore
from ai_usage.services.usage_store import UsageStore


class AppEnvironment:
    def __init__(self):
        self.settings = SettingsStore()
        self.secret_store = SecretStore()
        self.usage_store = UsageStore()
        self.log_store = LogStore()
        self.notification_service = NotificationService(self.usage_store)

        self.claude_provider = ClaudeProvider(self.log_store)
        self.codex_provider = CodexProvider(self.log_store)
        self.copilot_provider = CopilotProvider(self.secret_store, self.log_store)

        self.snapshots: dict[ProviderID, ProviderSnapshot] = {}
        self.last_refresh_at_utc: datetime | None = None
        self.is_refreshing = False
        self.last_refresh_error: str | None = None

        self._tray: object | None = None
        self._panel_window: object | None = None
        self._settings_window: object | None = None
        self._refresh_timer_id: int | None = None

        persisted = self.usage_store.load_snapshots()
        if persisted:
            self.snapshots = persisted
            dates = [s.fetched_at_utc for s in persisted.values() if s.fetched_at_utc]
            self.last_refresh_at_utc = max(dates) if dates else None
        else:
            self._bootstrap_placeholder_state()

    @property
    def localizer(self) -> Localizer:
        return self.settings.localizer

    @property
    def visible_menu_bar_items(self) -> list[MenuBarSummaryItem]:
        prefs = self.settings.preferences
        items = []
        for provider in sorted(prefs.visible_providers, key=lambda p: p.value):
            fraction = self._menu_bar_fraction(provider)
            items.append(MenuBarSummaryItem(provider=provider, remaining_fraction=fraction))
        return items

    def start(self):
        from ai_usage.tray import TrayIcon
        from ai_usage.ui.panel_window import PanelWindow
        from ai_usage.ui.settings_window import SettingsWindow

        self._panel_window = PanelWindow(self)
        self._settings_window = SettingsWindow(self)
        self._tray = TrayIcon(self)

        self.log_store.append(category="app", message="Application started.")
        self._schedule_refresh_loop()

    def show_panel(self):
        if self._panel_window:
            self._panel_window.show_panel()

    def show_settings(self):
        if self._settings_window:
            self._settings_window.show_settings()

    def quit_app(self):
        self.log_store.append(category="app", message="Application terminated by user.")
        from gi.repository import Gtk
        Gtk.main_quit()

    def trigger_refresh(self):
        if self.is_refreshing:
            return
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def current_auth_state(self, provider: ProviderID) -> ProviderAuthState:
        if provider == ProviderID.CODEX:
            return self.codex_provider.current_auth_state()
        if provider == ProviderID.CLAUDE:
            return self.claude_provider.current_auth_state()
        return self.copilot_provider.current_auth_state()

    def clear_auth(self, provider: ProviderID):
        if provider == ProviderID.COPILOT:
            self.copilot_provider.clear_auth()
            self.log_store.append(category="copilot", message="Copilot credentials removed from keyring.")
        self._bootstrap_missing_snapshot(provider)
        self.usage_store.save_snapshots(self.snapshots)
        self._notify_ui()

    def is_stale(self, reference_date: datetime | None = None) -> bool:
        if self.last_refresh_at_utc is None:
            return False
        ref = reference_date or datetime.now(timezone.utc)
        return (ref - self.last_refresh_at_utc).total_seconds() >= self.settings.staleness_threshold

    def _do_refresh(self):
        self.is_refreshing = True
        now = datetime.now(timezone.utc)
        self.log_store.append(category="refresh", message=f"Refresh started for {len(self._providers)} providers.")

        previous_snapshots = dict(self.snapshots)
        updated: dict[ProviderID, ProviderSnapshot] = {}
        errors: list[str] = []

        for provider in self._providers:
            snapshot = provider.refresh(now)
            updated[snapshot.provider] = snapshot
            level = "error" if snapshot.fetch_state == ProviderFetchState.FAILED else "info"
            self.log_store.append(
                level=level,
                category="refresh",
                message=f"{snapshot.provider.value} -> {snapshot.fetch_state.value}, auth={snapshot.auth_state.value}, metrics={len(snapshot.metrics)}",
            )
            if snapshot.error_description and snapshot.fetch_state == ProviderFetchState.FAILED:
                errors.append(f"{snapshot.provider.value.capitalize()}: {snapshot.error_description}")

        self.snapshots = updated
        self.last_refresh_at_utc = now
        self.last_refresh_error = "\n".join(errors) if errors else None

        if self.last_refresh_error:
            self.log_store.append(level="error", category="refresh", message=f"Refresh completed with errors: {self.last_refresh_error}")
        else:
            self.log_store.append(category="refresh", message="Refresh completed successfully.")

        self.usage_store.save_snapshots(updated)
        self.notification_service.process_refresh(previous_snapshots, updated, self.settings.preferences, now)

        self.is_refreshing = False
        GLib.idle_add(self._notify_ui)

    def _notify_ui(self):
        if self._tray:
            self._tray.update()
        if self._panel_window and self._panel_window.get_visible():
            self._panel_window.refresh_ui()

    def _schedule_refresh_loop(self):
        if self._refresh_timer_id:
            GLib.source_remove(self._refresh_timer_id)
            self._refresh_timer_id = None

        self.trigger_refresh()

        interval_seconds = self.settings.preferences.refresh_interval_minutes * 60
        self._refresh_timer_id = GLib.timeout_add_seconds(interval_seconds, self._on_refresh_timer)

        self.settings.on_change(self._on_settings_changed)

    def _on_refresh_timer(self) -> bool:
        self.trigger_refresh()
        return True

    def _on_settings_changed(self, old: DisplayPreferences, new: DisplayPreferences):
        if old.refresh_interval_minutes != new.refresh_interval_minutes:
            if self._refresh_timer_id:
                GLib.source_remove(self._refresh_timer_id)
            interval_seconds = new.refresh_interval_minutes * 60
            self._refresh_timer_id = GLib.timeout_add_seconds(interval_seconds, self._on_refresh_timer)
        self._notify_ui()

    @property
    def _providers(self) -> list:
        return [self.codex_provider, self.claude_provider, self.copilot_provider]

    def _menu_bar_fraction(self, provider: ProviderID) -> float | None:
        snapshot = self.snapshots.get(provider)
        if snapshot is None:
            return None
        prefs = self.settings.preferences
        if provider == ProviderID.CODEX:
            metric = snapshot.metric(prefs.codex_menu_bar_metric.usage_metric_kind)
        elif provider == ProviderID.CLAUDE:
            metric = snapshot.metric(prefs.claude_menu_bar_metric.usage_metric_kind)
        else:
            metric = snapshot.metric(UsageMetricKind.COPILOT_MONTHLY)
        return metric.remaining_fraction if metric else None

    def _bootstrap_placeholder_state(self):
        now = datetime.now(timezone.utc)
        self.snapshots[ProviderID.CODEX] = ProviderSnapshot(
            provider=ProviderID.CODEX,
            metrics=[
                UsageMetric(kind=UsageMetricKind.CODEX_FIVE_HOUR, last_updated_at_utc=now),
                UsageMetric(kind=UsageMetricKind.CODEX_WEEKLY, last_updated_at_utc=now),
                UsageMetric(kind=UsageMetricKind.CODEX_SPARK_FIVE_HOUR, last_updated_at_utc=now),
                UsageMetric(kind=UsageMetricKind.CODEX_SPARK_WEEKLY, last_updated_at_utc=now),
                UsageMetric(kind=UsageMetricKind.CODEX_CREDITS, unit=MetricUnit.CREDITS, last_updated_at_utc=now),
            ],
        )
        self.snapshots[ProviderID.CLAUDE] = ProviderSnapshot(
            provider=ProviderID.CLAUDE,
            metrics=[
                UsageMetric(kind=UsageMetricKind.CLAUDE_FIVE_HOUR, last_updated_at_utc=now),
                UsageMetric(kind=UsageMetricKind.CLAUDE_WEEKLY, last_updated_at_utc=now),
            ],
        )
        self.snapshots[ProviderID.COPILOT] = ProviderSnapshot(
            provider=ProviderID.COPILOT,
            metrics=[
                UsageMetric(kind=UsageMetricKind.COPILOT_MONTHLY, unit=MetricUnit.REQUESTS, last_updated_at_utc=now),
            ],
        )

    def _bootstrap_missing_snapshot(self, provider: ProviderID):
        now = datetime.now(timezone.utc)
        auth = self.current_auth_state(provider)
        fetch = ProviderFetchState.MISSING_AUTH if auth == ProviderAuthState.SIGNED_OUT else ProviderFetchState.FAILED

        if provider == ProviderID.CODEX:
            self.snapshots[ProviderID.CODEX] = ProviderSnapshot(
                provider=ProviderID.CODEX,
                auth_state=auth,
                fetch_state=fetch,
                metrics=[
                    UsageMetric(kind=UsageMetricKind.CODEX_FIVE_HOUR, last_updated_at_utc=now),
                    UsageMetric(kind=UsageMetricKind.CODEX_WEEKLY, last_updated_at_utc=now),
                    UsageMetric(kind=UsageMetricKind.CODEX_SPARK_FIVE_HOUR, last_updated_at_utc=now),
                    UsageMetric(kind=UsageMetricKind.CODEX_SPARK_WEEKLY, last_updated_at_utc=now),
                    UsageMetric(kind=UsageMetricKind.CODEX_CREDITS, unit=MetricUnit.CREDITS, last_updated_at_utc=now),
                ],
            )
        elif provider == ProviderID.CLAUDE:
            self.snapshots[ProviderID.CLAUDE] = ProviderSnapshot(
                provider=ProviderID.CLAUDE,
                auth_state=auth,
                fetch_state=fetch,
                metrics=[
                    UsageMetric(kind=UsageMetricKind.CLAUDE_FIVE_HOUR, last_updated_at_utc=now),
                    UsageMetric(kind=UsageMetricKind.CLAUDE_WEEKLY, last_updated_at_utc=now),
                ],
            )
        elif provider == ProviderID.COPILOT:
            self.snapshots[ProviderID.COPILOT] = ProviderSnapshot(
                provider=ProviderID.COPILOT,
                auth_state=auth,
                fetch_state=fetch,
                metrics=[
                    UsageMetric(kind=UsageMetricKind.COPILOT_MONTHLY, unit=MetricUnit.REQUESTS, last_updated_at_utc=now),
                ],
            )
