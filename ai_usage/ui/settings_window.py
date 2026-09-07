from __future__ import annotations

import subprocess
import threading
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from ai_usage.domain.localization import L10nKey
from ai_usage.domain.models import (
    AppLanguage,
    ClaudeMenuBarMetric,
    CodexMenuBarMetric,
    ProviderID,
)
from ai_usage.providers.copilot_provider import CopilotDeviceFlow

if TYPE_CHECKING:
    from ai_usage.app import AppEnvironment


class SettingsWindow(Gtk.Window):
    def __init__(self, env: AppEnvironment):
        super().__init__(title="Settings")
        self._env = env
        self._status_label = None

        self.set_default_size(700, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self._on_delete)

        self._notebook = Gtk.Notebook()
        self._build_tabs()
        self.add(self._notebook)

    def _on_delete(self, widget, event):
        self.hide()
        return True

    def show_settings(self):
        self._rebuild()
        self.show_all()
        self.present()

    def _rebuild(self):
        while self._notebook.get_n_pages() > 0:
            self._notebook.remove_page(0)
        self._build_tabs()
        self.show_all()

    def _build_tabs(self):
        loc = self._env.localizer
        self._notebook.append_page(self._build_accounts_tab(), Gtk.Label(label=loc.text(L10nKey.SETTINGS_TAB_ACCOUNTS)))
        self._notebook.append_page(self._build_display_tab(), Gtk.Label(label=loc.text(L10nKey.SETTINGS_TAB_DISPLAY)))
        self._notebook.append_page(self._build_notifications_tab(), Gtk.Label(label=loc.text(L10nKey.SETTINGS_TAB_NOTIFICATIONS)))
        self._notebook.append_page(self._build_logs_tab(), Gtk.Label(label=loc.text(L10nKey.SETTINGS_TAB_LOGS)))
        self._notebook.append_page(self._build_about_tab(), Gtk.Label(label=loc.text(L10nKey.SETTINGS_TAB_ABOUT)))

    def _build_accounts_tab(self) -> Gtk.Widget:
        loc = self._env.localizer
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        for provider in [ProviderID.CLAUDE, ProviderID.CODEX, ProviderID.COPILOT]:
            frame = Gtk.Frame()
            frame.set_shadow_type(Gtk.ShadowType.IN)
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            inner.set_margin_start(12)
            inner.set_margin_end(12)
            inner.set_margin_top(10)
            inner.set_margin_bottom(10)

            auth_state = self._env.current_auth_state(provider)
            status = loc.text(L10nKey.PROVIDER_STATUS_OK) if auth_state.value != "signedOut" else loc.text(L10nKey.SIGNED_OUT)
            hdr = Gtk.Label()
            hdr.set_markup(f"<b>{loc.provider_display_name(provider)}</b> — {status}")
            hdr.set_xalign(0)
            inner.pack_start(hdr, False, False, 0)

            if provider == ProviderID.CLAUDE:
                if auth_state.value == "signedOut":
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.CLAUDE_SESSION_HELP), wrap=True, xalign=0), False, False, 0)
                    btn = Gtk.Button(label=loc.text(L10nKey.REFRESH_NOW))
                    btn.connect("clicked", lambda _: self._env.trigger_refresh())
                    inner.pack_start(btn, False, False, 0)
                else:
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.CLAUDE_CLI_CONNECTED), wrap=True, xalign=0), False, False, 0)

            elif provider == ProviderID.CODEX:
                if auth_state.value == "signedOut":
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.CODEX_SESSION_HELP), wrap=True, xalign=0), False, False, 0)
                    btn = Gtk.Button(label=loc.text(L10nKey.REFRESH_NOW))
                    btn.connect("clicked", lambda _: self._env.trigger_refresh())
                    inner.pack_start(btn, False, False, 0)
                else:
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.CODEX_CLI_CONNECTED), wrap=True, xalign=0), False, False, 0)

            elif provider == ProviderID.COPILOT:
                inner.pack_start(Gtk.Label(label=loc.text(L10nKey.COPILOT_PAT_HELP), wrap=True, xalign=0), False, False, 0)
                if auth_state.value == "signedOut":
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.COPILOT_PLAN_HELP), wrap=True, xalign=0), False, False, 0)
                    btn = Gtk.Button(label=loc.text(L10nKey.SIGN_IN_TO_GITHUB_COPILOT))
                    btn.connect("clicked", self._on_copilot_sign_in)
                    inner.pack_start(btn, False, False, 0)
                else:
                    inner.pack_start(Gtk.Label(label=loc.text(L10nKey.COPILOT_CONNECTED_HELP), wrap=True, xalign=0), False, False, 0)
                    btn = Gtk.Button(label=loc.text(L10nKey.SIGN_OUT))
                    btn.connect("clicked", self._on_copilot_sign_out)
                    inner.pack_start(btn, False, False, 0)

            frame.add(inner)
            box.pack_start(frame, False, False, 0)

        self._status_label = Gtk.Label()
        self._status_label.set_xalign(0)
        box.pack_end(self._status_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(box)
        return scrolled

    def _build_display_tab(self) -> Gtk.Widget:
        loc = self._env.localizer
        prefs = self._env.settings.preferences
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        # Language
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_box.pack_start(Gtk.Label(label=loc.text(L10nKey.LANGUAGE)), False, False, 0)
        lang_combo = Gtk.ComboBoxText()
        lang_combo.append("englishUS", "English (US)")
        lang_combo.append("polish", "Polski")
        lang_combo.set_active_id(prefs.language.value)
        lang_combo.connect("changed", self._on_language_changed)
        lang_box.pack_end(lang_combo, False, False, 0)
        box.pack_start(lang_box, False, False, 0)

        # Refresh interval
        ri_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ri_box.pack_start(Gtk.Label(label=loc.text(L10nKey.REFRESH_INTERVAL)), False, False, 0)
        ri_combo = Gtk.ComboBoxText()
        for val in ["1", "5", "10", "15"]:
            ri_combo.append(val, f"{val} min")
        ri_combo.set_active_id(str(prefs.refresh_interval_minutes))
        ri_combo.connect("changed", self._on_refresh_interval_changed)
        ri_box.pack_end(ri_combo, False, False, 0)
        box.pack_start(ri_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)

        # Tray provider visibility
        box.pack_start(Gtk.Label(label=f"<b>{loc.text(L10nKey.MENU_BAR_SECTION)}</b>", use_markup=True, xalign=0), False, False, 0)
        for p in ProviderID:
            cb = Gtk.CheckButton(label=loc.provider_display_name(p))
            cb.set_active(p in prefs.visible_providers)
            cb.connect("toggled", self._on_tray_visibility_toggled, p)
            box.pack_start(cb, False, False, 0)

        # Codex tray metric
        cm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cm_box.pack_start(Gtk.Label(label=loc.text(L10nKey.CODEX_MENU_BAR_METRIC)), False, False, 0)
        cm_combo = Gtk.ComboBoxText()
        cm_combo.append("weekly", loc.codex_menu_bar_metric_label(CodexMenuBarMetric.WEEKLY))
        cm_combo.append("fiveHour", loc.codex_menu_bar_metric_label(CodexMenuBarMetric.FIVE_HOUR))
        cm_combo.set_active_id(prefs.codex_menu_bar_metric.value)
        cm_combo.connect("changed", self._on_codex_metric_changed)
        cm_box.pack_end(cm_combo, False, False, 0)
        box.pack_start(cm_box, False, False, 0)

        # Claude tray metric
        clm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        clm_box.pack_start(Gtk.Label(label=loc.text(L10nKey.CLAUDE_MENU_BAR_METRIC)), False, False, 0)
        clm_combo = Gtk.ComboBoxText()
        clm_combo.append("weekly", loc.claude_menu_bar_metric_label(ClaudeMenuBarMetric.WEEKLY))
        clm_combo.append("fiveHour", loc.claude_menu_bar_metric_label(ClaudeMenuBarMetric.FIVE_HOUR))
        clm_combo.set_active_id(prefs.claude_menu_bar_metric.value)
        clm_combo.connect("changed", self._on_claude_metric_changed)
        clm_box.pack_end(clm_combo, False, False, 0)
        box.pack_start(clm_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)

        # Panel provider visibility
        box.pack_start(Gtk.Label(label=f"<b>{loc.text(L10nKey.MAIN_PANEL_SECTION)}</b>", use_markup=True, xalign=0), False, False, 0)
        for p in ProviderID:
            cb = Gtk.CheckButton(label=loc.provider_display_name(p))
            cb.set_active(p in prefs.visible_panel_providers)
            cb.connect("toggled", self._on_panel_visibility_toggled, p)
            box.pack_start(cb, False, False, 0)

        # Codex Spark toggle
        spark_cb = Gtk.CheckButton(label=loc.text(L10nKey.SHOW_CODEX_SPARK_USAGE))
        spark_cb.set_active(prefs.show_codex_spark_usage)
        spark_cb.connect("toggled", self._on_spark_toggled)
        box.pack_start(spark_cb, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(box)
        return scrolled

    def _build_notifications_tab(self) -> Gtk.Widget:
        loc = self._env.localizer
        prefs = self._env.settings.preferences
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        box.pack_start(Gtk.Label(label=f"<b>{loc.text(L10nKey.USAGE_NOTIFICATIONS_SECTION)}</b>", use_markup=True, xalign=0), False, False, 0)

        ahead_cb = Gtk.CheckButton(label=loc.text(L10nKey.NOTIFICATIONS_AHEAD))
        ahead_cb.set_active(prefs.show_ahead_notifications)
        ahead_cb.set_tooltip_text(loc.text(L10nKey.NOTIFICATIONS_AHEAD_DESCRIPTION))
        ahead_cb.connect("toggled", lambda w: self._update_pref("show_ahead_notifications", w.get_active()))
        box.pack_start(ahead_cb, False, False, 0)

        behind_cb = Gtk.CheckButton(label=loc.text(L10nKey.NOTIFICATIONS_BEHIND))
        behind_cb.set_active(prefs.show_behind_notifications)
        behind_cb.set_tooltip_text(loc.text(L10nKey.NOTIFICATIONS_BEHIND_DESCRIPTION))
        behind_cb.connect("toggled", lambda w: self._update_pref("show_behind_notifications", w.get_active()))
        box.pack_start(behind_cb, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)
        box.pack_start(Gtk.Label(label=f"<b>{loc.text(L10nKey.EARLY_RESET_NOTIFICATIONS_SECTION)}</b>", use_markup=True, xalign=0), False, False, 0)

        codex_reset_cb = Gtk.CheckButton(label=loc.text(L10nKey.NOTIFICATIONS_CODEX_RESET))
        codex_reset_cb.set_active(prefs.show_codex_reset_notifications)
        codex_reset_cb.set_tooltip_text(loc.text(L10nKey.NOTIFICATIONS_CODEX_RESET_DESCRIPTION))
        codex_reset_cb.connect("toggled", lambda w: self._update_pref("show_codex_reset_notifications", w.get_active()))
        box.pack_start(codex_reset_cb, False, False, 0)

        claude_reset_cb = Gtk.CheckButton(label=loc.text(L10nKey.NOTIFICATIONS_CLAUDE_RESET))
        claude_reset_cb.set_active(prefs.show_claude_reset_notifications)
        claude_reset_cb.set_tooltip_text(loc.text(L10nKey.NOTIFICATIONS_CLAUDE_RESET_DESCRIPTION))
        claude_reset_cb.connect("toggled", lambda w: self._update_pref("show_claude_reset_notifications", w.get_active()))
        box.pack_start(claude_reset_cb, False, False, 0)

        return box

    def _build_logs_tab(self) -> Gtk.Widget:
        loc = self._env.localizer
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        entries = self._env.log_store.entries
        if not entries:
            log_box.pack_start(Gtk.Label(label=loc.text(L10nKey.NO_LOGS), xalign=0), False, False, 0)
        else:
            for entry in reversed(entries):
                ts = entry.timestamp_utc.strftime("%Y-%m-%d %H:%M:%S")
                text = f"[{ts}] [{entry.level.upper()}] [{entry.category}] {entry.message}"
                lbl = Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)
                lbl.set_line_wrap(True)
                log_box.pack_start(lbl, False, False, 0)

        scrolled.add(log_box)
        box.pack_start(scrolled, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        copy_btn = Gtk.Button(label=loc.text(L10nKey.COPY_LOGS))
        copy_btn.connect("clicked", self._on_copy_logs)
        btn_box.pack_end(copy_btn, False, False, 0)

        clear_btn = Gtk.Button(label=loc.text(L10nKey.CLEAR_LOGS))
        clear_btn.connect("clicked", self._on_clear_logs)
        btn_box.pack_end(clear_btn, False, False, 0)
        box.pack_start(btn_box, False, False, 0)

        return box

    def _build_about_tab(self) -> Gtk.Widget:
        from ai_usage import __version__
        loc = self._env.localizer
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(20)
        box.set_margin_bottom(20)

        title = Gtk.Label()
        title.set_markup(f"<big><b>{loc.text(L10nKey.MENU_BAR_APP_NAME)}</b></big>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        ver = Gtk.Label(label=f"{loc.text(L10nKey.APP_VERSION)} {__version__}")
        ver.set_xalign(0)
        box.pack_start(ver, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)

        legal_hdr = Gtk.Label()
        legal_hdr.set_markup(f"<b>{loc.text(L10nKey.LEGAL_SECTION)}</b>")
        legal_hdr.set_xalign(0)
        box.pack_start(legal_hdr, False, False, 0)

        disclaimer = Gtk.Label(label=loc.text(L10nKey.LOGO_DISCLAIMER), wrap=True, xalign=0)
        box.pack_start(disclaimer, False, False, 0)

        return box

    # -- callbacks --

    def _on_language_changed(self, combo):
        lang_id = combo.get_active_id()
        if lang_id:
            prefs = self._env.settings.preferences
            prefs.language = AppLanguage(lang_id)
            self._env.settings.preferences = prefs
            self._rebuild()

    def _on_refresh_interval_changed(self, combo):
        val = combo.get_active_id()
        if val:
            prefs = self._env.settings.preferences
            prefs.refresh_interval_minutes = int(val)
            self._env.settings.preferences = prefs

    def _on_tray_visibility_toggled(self, widget, provider):
        prefs = self._env.settings.preferences
        vis = prefs.visible_providers
        if widget.get_active():
            vis.add(provider)
        elif len(vis) > 1:
            vis.discard(provider)
        prefs.visible_providers = vis
        self._env.settings.preferences = prefs

    def _on_panel_visibility_toggled(self, widget, provider):
        prefs = self._env.settings.preferences
        vis = prefs.visible_panel_providers
        if widget.get_active():
            vis.add(provider)
        elif len(vis) > 1:
            vis.discard(provider)
        prefs.visible_panel_providers = vis
        self._env.settings.preferences = prefs

    def _on_codex_metric_changed(self, combo):
        val = combo.get_active_id()
        if val:
            prefs = self._env.settings.preferences
            prefs.codex_menu_bar_metric = CodexMenuBarMetric(val)
            self._env.settings.preferences = prefs

    def _on_claude_metric_changed(self, combo):
        val = combo.get_active_id()
        if val:
            prefs = self._env.settings.preferences
            prefs.claude_menu_bar_metric = ClaudeMenuBarMetric(val)
            self._env.settings.preferences = prefs

    def _on_spark_toggled(self, widget):
        prefs = self._env.settings.preferences
        prefs.show_codex_spark_usage = widget.get_active()
        self._env.settings.preferences = prefs

    def _update_pref(self, attr: str, value):
        prefs = self._env.settings.preferences
        setattr(prefs, attr, value)
        self._env.settings.preferences = prefs

    def _on_copilot_sign_in(self, _widget):
        loc = self._env.localizer
        if self._status_label:
            self._status_label.set_text("...")

        def _flow():
            try:
                device_code_resp = CopilotDeviceFlow.request_device_code()
                user_code = device_code_resp.get("user_code", "")
                verification_uri = device_code_resp.get("verification_uri", "")
                interval = device_code_resp.get("interval", 5)

                GLib.idle_add(self._set_status, loc.formatted(L10nKey.COPILOT_DEVICE_FLOW_WAITING, user_code))

                try:
                    subprocess.Popen(["xdg-open", verification_uri])
                except Exception:
                    pass

                token = CopilotDeviceFlow.poll_for_token(device_code_resp.get("device_code", ""), interval)
                self._env.copilot_provider.save_token(token)
                GLib.idle_add(self._set_status, loc.text(L10nKey.COPILOT_DEVICE_FLOW_CONNECTED))
                GLib.idle_add(self._env.trigger_refresh)
                GLib.idle_add(self._rebuild)
            except Exception as e:
                GLib.idle_add(self._set_status, str(e))

        threading.Thread(target=_flow, daemon=True).start()

    def _on_copilot_sign_out(self, _widget):
        self._env.clear_auth(ProviderID.COPILOT)
        self._rebuild()

    def _on_copy_logs(self, _widget):
        loc = self._env.localizer
        text = self._env.log_store.export_text
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text if text else loc.text(L10nKey.NO_LOGS), -1)
        self._set_status(loc.text(L10nKey.LOGS_COPIED) if text else loc.text(L10nKey.NO_LOGS))

    def _on_clear_logs(self, _widget):
        self._env.log_store.clear()
        self._rebuild()

    def _set_status(self, text: str):
        if self._status_label:
            self._status_label.set_text(text)
