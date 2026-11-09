"""Group events by day (pure logic, no GUI)."""

import datetime as dt
from typing import Iterable

from .models import Event


def group_by_day(first_day: dt.date, days: int, events: Iterable[Event]):
    """Return [(day, [Event, ...]), ...] for `days` consecutive days.

    Events outside the period are ignored. Within a day, all-day events come
    before events with the same start time.
    """
    grouped = {first_day + dt.timedelta(days=i): [] for i in range(days)}
    for event in events:
        key = event.start.date()
        if key in grouped:
            grouped[key].append(event)
    for items in grouped.values():
        items.sort(key=lambda e: (e.start, not e.all_day))
    return list(grouped.items())
