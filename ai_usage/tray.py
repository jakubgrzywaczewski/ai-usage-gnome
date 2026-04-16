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

from gi.repository import Gtk, GLib

from ai_usage.domain.localization import L10nKey
from ai_usage.domain.models import ProviderID
from ai_usage.ui.provider_widgets import percentage_text

if TYPE_CHECKING:
    from ai_usage.app import AppEnvironment


def _resources_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "resources")


class TrayIcon:
    def __init__(self, env: AppEnvironment):
        self._env = env
        self._indicator = None

        if _HAS_INDICATOR:
            icon_path = os.path.join(_resources_dir(), "app-icon.svg")
            if not os.path.exists(icon_path):
                icon_path = "dialog-information"

            self._indicator = AppIndicator3.Indicator.new(
                "ai-usage",
                icon_path,
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

    def _build_menu(self):
        loc = self._env.localizer
        menu = Gtk.Menu()

        show_item = Gtk.MenuItem(label=loc.text(L10nKey.USAGE_PANEL_TITLE))
        show_item.connect("activate", lambda _: self._env.show_panel())
        menu.append(show_item)

        menu.append(Gtk.SeparatorMenuItem())

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

        if self._indicator:
            self._indicator.set_menu(menu)

    def _update_label(self):
        if not self._indicator:
            return

        items = self._env.visible_menu_bar_items
        if not items:
            self._indicator.set_label("AI Usage", "AI Usage")
            return

        parts = []
        abbrevs = {
            ProviderID.CLAUDE: "C",
            ProviderID.CODEX: "X",
            ProviderID.COPILOT: "G",
        }
        for item in items:
            abbr = abbrevs.get(item.provider, "?")
            pct = percentage_text(item.remaining_fraction)
            parts.append(f"{abbr}:{pct}")

        label = " ".join(parts)
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
