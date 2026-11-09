"""Dialog for creating a new event."""

import datetime as dt

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ..models import NewEvent


class NewEventDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="New event", transient_for=parent, modal=True)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(12)
        grid.set_margin_bottom(8)
        self.get_content_area().add(grid)

        # Title
        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text("Title")
        self.title_entry.set_activates_default(True)
        grid.attach(Gtk.Label(label="Title", xalign=0), 0, 0, 1, 1)
        grid.attach(self.title_entry, 1, 0, 3, 1)

        # Date
        self.calendar = Gtk.Calendar()
        grid.attach(Gtk.Label(label="Date", xalign=0, yalign=0), 0, 1, 1, 1)
        grid.attach(self.calendar, 1, 1, 3, 1)

        # All day
        self.all_day = Gtk.CheckButton(label="All day")
        self.all_day.connect("toggled", self._on_all_day_toggled)
        grid.attach(self.all_day, 1, 2, 3, 1)

        # Times
        now = dt.datetime.now()
        self.from_h = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.from_m = Gtk.SpinButton.new_with_range(0, 55, 5)
        self.to_h = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.to_m = Gtk.SpinButton.new_with_range(0, 55, 5)
        self.from_h.set_value((now.hour + 1) % 24)
        self.to_h.set_value((now.hour + 2) % 24)
        for spin in (self.from_h, self.from_m, self.to_h, self.to_m):
            spin.set_wrap(True)
            spin.set_width_chars(2)

        self._time_boxes = []
        grid.attach(Gtk.Label(label="From", xalign=0), 0, 3, 1, 1)
        grid.attach(self._time_box(self.from_h, self.from_m), 1, 3, 1, 1)
        grid.attach(Gtk.Label(label="To", xalign=0), 2, 3, 1, 1)
        grid.attach(self._time_box(self.to_h, self.to_m), 3, 3, 1, 1)

        self.show_all()

    def _time_box(self, hours, minutes):
        box = Gtk.Box(spacing=4)
        box.pack_start(hours, False, False, 0)
        box.pack_start(Gtk.Label(label=":"), False, False, 0)
        box.pack_start(minutes, False, False, 0)
        self._time_boxes.append(box)
        return box

    def _on_all_day_toggled(self, button):
        for box in self._time_boxes:
            box.set_sensitive(not button.get_active())

    def get_new_event(self) -> NewEvent:
        year, month, day = self.calendar.get_date()  # month is 0-based
        return NewEvent(
            title=self.title_entry.get_text().strip(),
            day=dt.date(year, month + 1, day),
            start_time=dt.time(int(self.from_h.get_value()),
                               int(self.from_m.get_value())),
            end_time=dt.time(int(self.to_h.get_value()),
                             int(self.to_m.get_value())),
            all_day=self.all_day.get_active(),
        )
