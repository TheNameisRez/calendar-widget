"""Simple dataclasses passed between the modules."""

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """An event to display (start time in the local time zone)."""
    start: dt.datetime
    all_day: bool
    title: str


@dataclass(frozen=True)
class NewEvent:
    """Input from the "New event" dialog."""
    title: str
    day: dt.date
    start_time: dt.time
    end_time: dt.time
    all_day: bool
