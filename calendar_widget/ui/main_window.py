"""Main window: a narrow desktop widget with the daily overview."""

import calendar
import datetime as dt
import locale
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from .. import config
from ..agenda import group_by_day
from ..auth import get_service
from ..calendar_api import create_event, fetch_events
from .new_event_dialog import NewEventDialog

STYLE_FILE = Path(__file__).with_name("style.css")


class CalendarWidget(Gtk.Window):
    def __init__(self):
        super().__init__(title="Calendar")
        self.service = None

        self._setup_window()
        self._load_style()
        self._build_layout()

        self.refresh()
        GLib.timeout_add_seconds(config.REFRESH_MINUTES * 60, self.refresh)

    # ---- Setup ------------------------------------------------------------

    def _setup_window(self):
        screen = Gdk.Screen.get_default()
        display = screen.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()

        width = int(geo.width * config.WIDTH_FRACTION)
        self.set_default_size(width, geo.height - 80)
        self.move(geo.x + geo.width - width - 10, geo.y + 40)

        self.set_decorated(False)
        self.set_keep_below(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.stick()

        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

    def _load_style(self):
        css = Gtk.CssProvider()
        css.load_from_path(str(STYLE_FILE))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_layout(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        outer.set_margin_start(12)
        outer.set_margin_end(12)
        outer.set_margin_top(10)
        outer.set_margin_bottom(10)
        self.add(outer)

        top = Gtk.Box()
        top.pack_start(self._label("Calendar", "day"), True, True, 0)
        plus = Gtk.Button(label="+")
        plus.get_style_context().add_class("plus")
        plus.set_tooltip_text("New event")
        plus.connect("clicked", self.on_new_event)
        top.pack_end(plus, False, False, 0)
        outer.pack_start(top, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scroller.add(self.box)
        outer.pack_start(scroller, True, True, 0)

    @staticmethod
    def _label(text, css_class, wrap=False):
        label = Gtk.Label(label=text, xalign=0)
        label.get_style_context().add_class(css_class)
        if wrap:
            label.set_line_wrap(True)
            label.set_max_width_chars(28)
        return label

    # ---- Actions ----------------------------------------------------------

    def on_new_event(self, _button):
        # Bring the widget to the front briefly so the dialog is visible.
        self.set_keep_below(False)
        dialog = NewEventDialog(self)
        response = dialog.run()
        new_event = dialog.get_new_event()
        dialog.destroy()
        self.set_keep_below(True)

        if response != Gtk.ResponseType.OK or not new_event.title:
            return

        try:
            if self.service is None:
                self.service = get_service()
            create_event(self.service, new_event)
        except Exception as ex:
            self._show_error("Could not save the event", str(ex))
            return
        self.refresh()

    def _show_error(self, title, details):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(details)
        dialog.run()
        dialog.destroy()

    def refresh(self):
        first_day, events, error = dt.date.today(), [], None
        try:
            if self.service is None:
                self.service = get_service()
            first_day, events = fetch_events(self.service, config.DAYS)
        except Exception as ex:
            error = str(ex)
            self.service = None  # reconnect on the next attempt

        for child in self.box.get_children():
            self.box.remove(child)

        if error:
            self.box.pack_start(
                self._label("Sync error: " + error, "empty", wrap=True),
                False, False, 0)

        for index, (day, day_events) in enumerate(
                group_by_day(first_day, config.DAYS, events)):
            self._add_day(index, day, day_events)

        self.box.show_all()
        return True  # keep the timer running

    def _add_day(self, index, day, day_events):
        weekday = calendar.day_name[day.weekday()]
        month = calendar.month_abbr[day.month]
        title = f"{weekday}, {day.day} {month}"
        if index == 0:
            title = "Today · " + title
        header = self._label(title, "day")
        if index == 0:
            header.get_style_context().add_class("today")
        self.box.pack_start(header, False, False, 0)

        if not day_events:
            self.box.pack_start(self._label("–", "empty"), False, False, 0)
            return

        for event in day_events:
            time_text = "all day" if event.all_day else event.start.strftime("%H:%M")
            row = Gtk.Box(spacing=8)
            time_label = self._label(time_text, "time")
            time_label.set_width_chars(9)
            row.pack_start(time_label, False, False, 0)
            row.pack_start(self._label(event.title, "event", wrap=True),
                           True, True, 0)
            self.box.pack_start(row, False, False, 0)


def run():
    try:
        # Weekday and month names in the system language
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass  # locale not installed -> English names

    window = CalendarWidget()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
