"""Entry point for AI Usage GNOME tray application."""

from __future__ import annotations

import signal


def main():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk

    GLib.set_application_name("AI Usage")
    GLib.set_prgname("ai-usage")

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    from ai_usage.app import AppEnvironment

    env = AppEnvironment()
    env.start()

    Gtk.main()


if __name__ == "__main__":
    main()
