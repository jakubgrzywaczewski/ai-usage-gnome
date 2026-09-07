from __future__ import annotations

from datetime import datetime

_MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "pl": ["sty", "lut", "mar", "kwi", "maj", "cze",
           "lip", "sie", "wrz", "paź", "lis", "gru"],
}


def format_reset_date(reset_at_utc: datetime, now: datetime, lang: str = "en") -> str:
    local_reset = reset_at_utc.astimezone()
    local_now = now.astimezone()

    if local_reset > local_now and local_reset.date() == local_now.date():
        return local_reset.strftime("%H:%M")

    months = _MONTHS.get(lang, _MONTHS["en"])
    month = months[local_reset.month - 1]
    return f"{local_reset.day:02d} {month} {local_reset.year}, {local_reset:%H:%M}"


def format_relative_time(dt: datetime, now: datetime, lang: str = "en") -> str:
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return _just_now(lang)
    if seconds < 60:
        return _just_now(lang)
    if seconds < 3600:
        minutes = seconds // 60
        if lang == "pl":
            return f"{minutes} min temu"
        return f"{minutes}m ago"
    if seconds < 86400:
        hours = seconds // 3600
        if lang == "pl":
            return f"{hours} godz. temu"
        return f"{hours}h ago"

    days = seconds // 86400
    if lang == "pl":
        return f"{days} dni temu"
    return f"{days}d ago"


def _just_now(lang: str) -> str:
    if lang == "pl":
        return "przed chwilą"
    return "just now"
