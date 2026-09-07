from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gtk

from ai_usage.domain.models import ProviderID


def _resources_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")


def theme_fg_rgb() -> tuple[float, float, float]:
    """The current theme's foreground colour, so brand glyphs stay visible in
    both light and dark themes."""
    rgba = Gtk.Label().get_style_context().get_color(Gtk.StateFlags.NORMAL)
    return (rgba.red, rgba.green, rgba.blue)


def _tint(pixbuf: GdkPixbuf.Pixbuf, rgb: tuple[float, float, float]) -> GdkPixbuf.Pixbuf:
    import cairo

    w, h = pixbuf.get_width(), pixbuf.get_height()
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_IN)
    cr.set_source_rgb(*rgb)
    cr.paint()
    return Gdk.pixbuf_get_from_surface(surface, 0, 0, w, h)


def load_provider_icon(
    provider: ProviderID, size: int = 24, tint: tuple[float, float, float] | None = None
) -> GdkPixbuf.Pixbuf | None:
    svg_path = os.path.join(_resources_dir(), f"{provider.icon_resource_name}.svg")
    if not os.path.exists(svg_path):
        return None
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(svg_path, size, size)
    except Exception:
        return None
    if tint is not None:
        try:
            return _tint(pixbuf, tint)
        except Exception:
            return pixbuf
    return pixbuf


def percentage_text(fraction: float | None) -> str:
    if fraction is None:
        return "-%"
    return f"{int(round(fraction * 100))}%"


def usage_percentage_text(remaining_fraction: float | None) -> str:
    """Render how much of a limit has been *used* from its remaining fraction."""
    if remaining_fraction is None:
        return "—"
    used = max(0.0, min(1.0, 1.0 - remaining_fraction))
    return f"{int(round(used * 100))}%"


class UsageBar(Gtk.DrawingArea):
    """A colored progress bar that fills up as a limit is consumed.

    ``remaining_fraction`` is what the API reports (1.0 == nothing used); the
    bar shows ``1 - remaining_fraction`` so a fuller bar means less headroom.
    """

    def __init__(self, remaining_fraction: float | None = None, height: int = 10):
        super().__init__()
        self._remaining = remaining_fraction
        self.set_size_request(-1, height)
        self.connect("draw", self._on_draw)

    def set_fraction(self, remaining_fraction: float | None):
        self._remaining = remaining_fraction
        self.queue_draw()

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.14)
        _rounded_rect(cr, 0, 0, w, h, h / 2)
        cr.fill()

        if self._remaining is not None:
            used = max(0.0, min(1.0, 1.0 - self._remaining))
            if used > 0.9:
                cr.set_source_rgba(0.9, 0.2, 0.2, 0.95)
            elif used > 0.7:
                cr.set_source_rgba(0.9, 0.8, 0.1, 0.95)
            else:
                cr.set_source_rgba(0.2, 0.8, 0.2, 0.95)
            _rounded_rect(cr, 0, 0, max(w * used, h if used > 0 else 0), h, h / 2)
            cr.fill()

        return False


# Backwards-compatible alias.
RemainingBar = UsageBar


class TimeBar(Gtk.DrawingArea):
    """A thin blue bar showing expected time remaining."""

    def __init__(self, fraction: float | None = None, height: int = 4):
        super().__init__()
        self._fraction = fraction
        self.set_size_request(-1, height)
        self.connect("draw", self._on_draw)

    def set_fraction(self, fraction: float | None):
        self._fraction = fraction
        self.queue_draw()

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.14)
        _rounded_rect(cr, 0, 0, w, h, h / 2)
        cr.fill()

        if self._fraction is not None:
            f = max(0.0, min(1.0, self._fraction))
            cr.set_source_rgba(0.3, 0.5, 0.9, 0.95)
            _rounded_rect(cr, 0, 0, w * f, h, h / 2)
            cr.fill()

        return False


def _rounded_rect(cr, x, y, w, h, r):
    import math
    if w <= 0:
        return
    r = min(r, h / 2, w / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def create_metric_card(
    title: str,
    value_text: str,
    remaining_fraction: float | None,
    reset_text: str | None,
    is_credits: bool = False,
    note: str | None = None,
) -> Gtk.Frame:
    frame = Gtk.Frame()
    frame.set_shadow_type(Gtk.ShadowType.NONE)
    frame.get_style_context().add_class("metric-card")

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.set_margin_start(14)
    box.set_margin_end(14)
    box.set_margin_top(12)
    box.set_margin_bottom(12)

    header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    title_label = Gtk.Label(label=title)
    title_label.set_xalign(0)
    title_label.get_style_context().add_class("metric-title")
    header.pack_start(title_label, True, True, 0)

    value_label = Gtk.Label(label=value_text)
    value_label.set_valign(Gtk.Align.CENTER)
    value_label.get_style_context().add_class("metric-value")
    header.pack_end(value_label, False, False, 0)
    box.pack_start(header, False, False, 0)

    if not is_credits and remaining_fraction is not None:
        box.pack_start(UsageBar(remaining_fraction), False, False, 0)

    if note:
        note_label = Gtk.Label(label=note)
        note_label.set_xalign(0)
        note_label.get_style_context().add_class("dim-label")
        box.pack_start(note_label, False, False, 0)

    if reset_text:
        reset_label = Gtk.Label(label=reset_text)
        reset_label.set_xalign(0)
        reset_label.get_style_context().add_class("dim-label")
        box.pack_start(reset_label, False, False, 0)

    frame.add(box)
    return frame
