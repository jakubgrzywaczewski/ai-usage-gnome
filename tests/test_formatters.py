from datetime import datetime, timedelta, timezone

from ai_usage.domain.formatters import format_relative_time, format_reset_date


def test_reset_date_uses_app_language_not_system_locale():
    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    future = datetime(2026, 9, 13, 16, 25, tzinfo=timezone.utc)

    assert "Sep" in format_reset_date(future, now, "en")
    assert "wrz" in format_reset_date(future, now, "pl")


def test_reset_date_shows_time_only_when_same_day():
    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    later_today = now + timedelta(hours=3)
    assert format_reset_date(later_today, now, "en") == later_today.astimezone().strftime("%H:%M")


def test_reset_date_unknown_language_falls_back_to_english():
    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    future = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
    assert "Dec" in format_reset_date(future, now, "de")


def test_relative_time():
    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    assert format_relative_time(now - timedelta(seconds=10), now, "en") == "just now"
    assert format_relative_time(now - timedelta(minutes=5), now, "en") == "5m ago"
    assert format_relative_time(now - timedelta(hours=2), now, "pl") == "2 godz. temu"
    assert format_relative_time(now - timedelta(days=3), now, "en") == "3d ago"
