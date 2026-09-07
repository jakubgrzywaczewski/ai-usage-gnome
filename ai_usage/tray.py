from __future__ import annotations

import os
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "3.0")

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    _HAS_INDICATOR = True
except (ValueError, ImportError):
    _HAS_INDICATOR = False

from gi.repository import Gtk

from ai_usage.domain.localization import L10nKey
from ai_usage.domain.models import ProviderID, UsageMetricKind

if TYPE_CHECKING:
    from ai_usage.app import AppEnvironment


def _resources_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "resources")


def _text_bar(used_fraction: float, width: int = 10) -> str:
    filled = max(0, min(width, int(round(used_fraction * width))))
    return "█" * filled + "░" * (width - filled)


class TrayIcon:
    def __init__(self, env: AppEnvironment):
        self._env = env
        self._indicator = None

        if _HAS_INDICATOR:
            # A "-symbolic" icon name lets GNOME recolor it to match the panel
            # (white on a dark theme, dark on a light theme).
            has_symbolic = os.path.exists(
                os.path.join(_resources_dir(), "ai-usage-symbolic.svg")
            )
            icon_name = "ai-usage-symbolic" if has_symbolic else "dialog-information"

            self._indicator = AppIndicator3.Indicator.new(
                "ai-usage",
                icon_name,
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self._indicator.set_icon_theme_path(_resources_dir())

            self._build_menu()
            self._update_label()
        else:
            self._build_fallback_status_icon()

    def update(self):
        self._update_label()
        if self._indicator:
            self._build_menu()

    def _row_kinds(self, provider: ProviderID) -> list:
        prefs = self._env.settings.preferences
        if provider == ProviderID.CLAUDE:
            return [UsageMetricKind.CLAUDE_FIVE_HOUR, UsageMetricKind.CLAUDE_WEEKLY]
        if provider == ProviderID.CODEX:
            kinds = [UsageMetricKind.CODEX_FIVE_HOUR, UsageMetricKind.CODEX_WEEKLY]
            if getattr(prefs, "show_codex_spark_usage", False):
                kinds += [UsageMetricKind.CODEX_SPARK_FIVE_HOUR, UsageMetricKind.CODEX_SPARK_WEEKLY]
            return kinds
        return [UsageMetricKind.COPILOT_MONTHLY]

    def _usage_rows(self) -> list[str]:
        loc = self._env.localizer
        prefs = self._env.settings.preferences
        rows: list[str] = []
        for provider in (ProviderID.CLAUDE, ProviderID.CODEX, ProviderID.COPILOT):
            if provider not in prefs.visible_providers:
                continue
            snapshot = self._env.snapshots.get(provider)
            if snapshot is None:
                continue
            for kind in self._row_kinds(provider):
                metric = snapshot.metric(kind)
                if metric is None:
                    continue
                name = loc.notification_metric_name(kind)
                rf = metric.remaining_fraction
                if rf is None:
                    rows.append(f"{name}   ·   {loc.text(L10nKey.NO_USAGE_DATA)}")
                else:
                    used = max(0.0, min(1.0, 1.0 - rf))
                    rows.append(f"{name}   {_text_bar(used)}  {int(round(used * 100))}%")
        return rows

    def _menu_item(self, label: str, icon_name: str, on_activate) -> Gtk.MenuItem:
        try:
            item = Gtk.ImageMenuItem(label=label)
            item.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU))
            item.set_always_show_image(True)
        except Exception:
            item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda _: on_activate())
        return item

    def _build_menu(self):
        loc = self._env.localizer
        menu = Gtk.Menu()

        for row in self._usage_rows():
            row_item = Gtk.MenuItem(label=row)
            row_item.connect("activate", lambda _: self._env.show_panel())
            menu.append(row_item)
        if menu.get_children():
            menu.append(Gtk.SeparatorMenuItem())

        open_item = self._menu_item(
            loc.text(L10nKey.USAGE_PANEL_TITLE),
            "utilities-system-monitor-symbolic",
            self._env.show_panel,
        )
        menu.append(open_item)

        menu.append(self._menu_item(
            loc.text(L10nKey.MENU_ACTION_REFRESH),
            "view-refresh-symbolic",
            self._env.trigger_refresh,
        ))
        menu.append(self._menu_item(
            loc.text(L10nKey.MENU_ACTION_SETTINGS),
            "preferences-system-symbolic",
            self._env.show_settings,
        ))

        menu.append(Gtk.SeparatorMenuItem())

        menu.append(self._menu_item(
            loc.text(L10nKey.QUIT_APP),
            "application-exit-symbolic",
            self._env.quit_app,
        ))

        menu.show_all()

        if self._indicator:
            self._indicator.set_menu(menu)
            try:
                self._indicator.set_secondary_activate_target(open_item)
            except Exception:
                pass

    def _update_label(self):
        if not self._indicator:
            return

        items = self._env.visible_menu_bar_items
        if not items:
            self._indicator.set_label("AI", "AI")
            return

        multi = len(items) > 1
        names = {
            ProviderID.CLAUDE: "Claude",
            ProviderID.CODEX: "Codex",
            ProviderID.COPILOT: "Copilot",
        }
        parts = []
        for item in items:
            frac = item.remaining_fraction
            if frac is None:
                pct = "—"
            else:
                used = max(0, min(100, int(round((1.0 - frac) * 100))))
                pct = f"{used}%"
            if multi:
                parts.append(f"{names.get(item.provider, 'AI')} {pct}")
            else:
                parts.append(pct)

        label = "AI " + "  ".join(parts)
        self._indicator.set_label(label, label)

    def _build_fallback_status_icon(self):
        """Fallback for systems without AppIndicator3."""
        loc = self._env.localizer
        menu = Gtk.Menu()

        show_item = Gtk.MenuItem(label=loc.text(L10nKey.USAGE_PANEL_TITLE))
        show_item.connect("activate", lambda _: self._env.show_panel())
        menu.append(show_item)

        refresh_item = Gtk.MenuItem(label=loc.text(L10nKey.MENU_ACTION_REFRESH))
        refresh_item.connect("activate", lambda _: self._env.trigger_refresh())
        menu.append(refresh_item)

        settings_item = Gtk.MenuItem(label=loc.text(L10nKey.MENU_ACTION_SETTINGS))
        settings_item.connect("activate", lambda _: self._env.show_settings())
        menu.append(settings_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label=loc.text(L10nKey.QUIT_APP))
        quit_item.connect("activate", lambda _: self._env.quit_app())
        menu.append(quit_item)

        menu.show_all()
