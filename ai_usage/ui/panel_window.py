from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from ai_usage.domain.formatters import format_relative_time, format_reset_date
from ai_usage.domain.localization import L10nKey
from ai_usage.domain.models import (
    ProviderFetchState,
    ProviderID,
    UsageMetricKind,
)
from ai_usage.ui.provider_widgets import (
    create_metric_card,
    load_provider_icon,
    theme_fg_rgb,
    usage_percentage_text,
)

if TYPE_CHECKING:
    from ai_usage.app import AppEnvironment

_CSS = b"""
.panel-window {
    background-color: @theme_bg_color;
    border-radius: 12px;
}
.metric-card {
    background-color: alpha(@theme_fg_color, 0.07);
    border-radius: 10px;
}
.metric-title {
    font-size: 13px;
    font-weight: 500;
}
.metric-value {
    font-size: 15px;
    font-weight: 700;
    font-feature-settings: "tnum";
}
.dim-label {
    font-size: 11px;
    opacity: 0.6;
}
.provider-header {
    font-size: 14px;
    font-weight: 700;
}
.error-label {
    color: @error_color;
    font-size: 12px;
}
"""


class PanelWindow(Gtk.Window):
    def __init__(self, env: AppEnvironment):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self._env = env
        self._timer_id = None

        self.set_title("AI Usage")
        self.set_default_size(420, -1)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self._on_delete)

        css = Gtk.CssProvider()
        css.load_from_data(_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self._content_box.set_margin_start(16)
        self._content_box.set_margin_end(16)
        self._content_box.set_margin_top(16)
        self._content_box.set_margin_bottom(16)
        self._content_box.get_style_context().add_class("panel-window")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_max_content_height(700)
        scrolled.set_propagate_natural_height(True)
        scrolled.add(self._content_box)
        self.add(scrolled)

        self._build()

    def _on_delete(self, widget, event):
        self.hide()
        return True

    def refresh_ui(self):
        self._build()

    def show_panel(self):
        self._build()
        self.show_all()
        self.present()
        self._start_timer()

    def hide_panel(self):
        self._stop_timer()
        self.hide()

    def _start_timer(self):
        self._stop_timer()
        self._timer_id = GLib.timeout_add_seconds(1, self._tick)

    def _stop_timer(self):
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _tick(self):
        if self.get_visible():
            self._update_footer()
            return True
        self._stop_timer()
        return False

    def _build(self):
        for child in self._content_box.get_children():
            self._content_box.remove(child)

        loc = self._env.localizer
        now = datetime.now(timezone.utc)

        prefs = self._env.settings.preferences
        visible = sorted(prefs.visible_panel_providers, key=lambda p: p.value)

        for provider in visible:
            self._build_provider(provider, now)

        self._footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._footer_box.set_margin_top(2)

        settings_btn = Gtk.Button(label=loc.text(L10nKey.OPEN_SETTINGS))
        settings_btn.connect("clicked", lambda _: self._env.show_settings())
        self._footer_box.pack_start(settings_btn, False, False, 0)

        self._last_update_label = Gtk.Label()
        self._last_update_label.set_xalign(1)
        self._last_update_label.get_style_context().add_class("dim-label")
        self._footer_box.pack_start(self._last_update_label, True, True, 0)

        refresh_btn = Gtk.Button(label=loc.text(L10nKey.REFRESH_NOW))
        refresh_btn.connect("clicked", lambda _: self._env.trigger_refresh())
        self._footer_box.pack_end(refresh_btn, False, False, 0)

        self._content_box.pack_start(self._footer_box, False, False, 0)
        self._update_footer()
        self.show_all()

    def _build_provider(self, provider: ProviderID, now: datetime):
        loc = self._env.localizer
        snapshot = self._env.snapshots.get(provider)
        prefs = self._env.settings.preferences

        prov_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = load_provider_icon(provider, 18, tint=theme_fg_rgb())
        if icon:
            img = Gtk.Image.new_from_pixbuf(icon)
            hdr.pack_start(img, False, False, 0)
        name_label = Gtk.Label(label=loc.provider_display_name(provider))
        name_label.set_xalign(0)
        name_label.get_style_context().add_class("provider-header")
        hdr.pack_start(name_label, True, True, 0)

        link_btn = Gtk.LinkButton.new_with_label(provider.usage_settings_url, "↗")
        link_btn.set_relief(Gtk.ReliefStyle.NONE)
        link_btn.set_tooltip_text(loc.text(L10nKey.OPEN_PROVIDER_USAGE_PAGE))
        hdr.pack_end(link_btn, False, False, 0)

        prov_box.pack_start(hdr, False, False, 0)

        if snapshot and snapshot.fetch_state == ProviderFetchState.MISSING_AUTH:
            lbl = Gtk.Label(label=f"{loc.provider_display_name(provider)}: {loc.text(L10nKey.AUTHENTICATION_REQUIRED)}")
            lbl.set_xalign(0)
            lbl.get_style_context().add_class("dim-label")
            prov_box.pack_start(lbl, False, False, 0)
        elif snapshot and snapshot.fetch_state == ProviderFetchState.FAILED:
            lbl = Gtk.Label(label=snapshot.error_description or loc.text(L10nKey.FETCH_FAILED))
            lbl.set_xalign(0)
            lbl.get_style_context().add_class("error-label")
            prov_box.pack_start(lbl, False, False, 0)

        if snapshot and snapshot.fetch_state != ProviderFetchState.MISSING_AUTH:
            for kind in self._metrics_for(provider):
                metric = snapshot.metric(kind) if snapshot else None
                is_credits = kind == UsageMetricKind.CODEX_CREDITS

                has_data = metric is not None and (
                    metric.remaining_fraction is not None or metric.remaining_value is not None
                )
                note = None if (has_data or is_credits) else loc.text(L10nKey.NO_USAGE_DATA)

                card = create_metric_card(
                    title=loc.metric_title(kind),
                    value_text="—" if note else self._value_text(kind, metric),
                    remaining_fraction=metric.remaining_fraction if metric else None,
                    reset_text=self._reset_text(metric, now) if has_data else None,
                    is_credits=is_credits,
                    note=note,
                )
                prov_box.pack_start(card, False, False, 0)

        self._content_box.pack_start(prov_box, False, False, 0)

    def _metrics_for(self, provider: ProviderID) -> list[UsageMetricKind]:
        if provider == ProviderID.CLAUDE:
            return [UsageMetricKind.CLAUDE_FIVE_HOUR, UsageMetricKind.CLAUDE_WEEKLY]
        if provider == ProviderID.CODEX:
            metrics = [UsageMetricKind.CODEX_FIVE_HOUR, UsageMetricKind.CODEX_WEEKLY]
            if self._env.settings.preferences.show_codex_spark_usage:
                metrics.extend([UsageMetricKind.CODEX_SPARK_FIVE_HOUR, UsageMetricKind.CODEX_SPARK_WEEKLY])
            metrics.append(UsageMetricKind.CODEX_CREDITS)
            return metrics
        return [UsageMetricKind.COPILOT_MONTHLY]

    def _value_text(self, kind: UsageMetricKind, metric) -> str:
        loc = self._env.localizer
        if metric is None:
            return "-" if kind == UsageMetricKind.CODEX_CREDITS else loc.text(L10nKey.NO_USAGE_DATA)
        if metric.unit.value in ("percentage", "requests"):
            if metric.remaining_fraction is not None:
                return usage_percentage_text(metric.remaining_fraction)
            return loc.text(L10nKey.NO_USAGE_DATA)
        elif metric.unit.value == "credits":
            if metric.remaining_value is not None:
                return str(int(round(metric.remaining_value)))
        return "-"

    def _reset_text(self, metric, now: datetime) -> str | None:
        loc = self._env.localizer
        if metric is None:
            return loc.text(L10nKey.AUTHENTICATION_REQUIRED)
        if metric.reset_at_utc is None:
            return None
        lang = "pl" if self._env.settings.preferences.language.value == "polish" else "en"
        return f"{loc.text(L10nKey.RESET_AT)}: {format_reset_date(metric.reset_at_utc, now, lang)}"

    def _update_footer(self):
        if not hasattr(self, "_last_update_label"):
            return
        loc = self._env.localizer
        now = datetime.now(timezone.utc)
        last = self._env.last_refresh_at_utc
        lang = "pl" if self._env.settings.preferences.language.value == "polish" else "en"
        if last:
            self._last_update_label.set_text(f"{loc.text(L10nKey.LAST_UPDATE)}: {format_relative_time(last, now, lang)}")
        else:
            self._last_update_label.set_text(f"{loc.text(L10nKey.LAST_UPDATE)}: {loc.text(L10nKey.NOT_CONFIGURED)}")
