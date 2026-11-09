"""Access to the Google Calendar API: fetch and create events.

This module deliberately imports neither GTK nor the Google libraries. It only
works with the `service` object it is given, which makes it easy to test.
"""

import datetime as dt

from .config import DAYS
from .models import Event, NewEvent


def _local_midnight(day: dt.date) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.min).astimezone()


def fetch_events(service, days: int = DAYS):
    """Fetch the events of all calendars for the next `days` days.

    Returns: (first day, list of Event sorted by start time).
    """
    first_day = dt.date.today()
    time_min = _local_midnight(first_day)
    time_max = _local_midnight(first_day + dt.timedelta(days=days))

    calendars = service.calendarList().list().execute().get("items", [])
    events = []
    errors = []

    for cal in calendars:
        try:
            result = service.events().list(
                calendarId=cal["id"],
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        except Exception as ex:  # a single calendar could not be read
            errors.append(str(ex))
            continue

        for item in result.get("items", []):
            raw = item["start"].get("dateTime", item["start"].get("date"))
            all_day = "dateTime" not in item["start"]
            start = dt.datetime.fromisoformat(raw).astimezone()
            events.append(Event(start, all_day, item.get("summary", "(no title)")))

    if errors and not events and len(errors) == len(calendars):
        raise RuntimeError(errors[0])

    events.sort(key=lambda e: (e.start, not e.all_day))
    return first_day, events


def build_event_body(new: NewEvent) -> dict:
    """Build the request body for events().insert()."""
    if new.all_day:
        return {
            "summary": new.title,
            "start": {"date": new.day.isoformat()},
            # For all-day events the end date is exclusive.
            "end": {"date": (new.day + dt.timedelta(days=1)).isoformat()},
        }

    # Naive time -> the computer's local time zone, including the UTC offset.
    # Google then does not need a separate time zone name.
    start = dt.datetime.combine(new.day, new.start_time).astimezone()
    end = dt.datetime.combine(new.day, new.end_time).astimezone()
    if end <= start:
        end = start + dt.timedelta(hours=1)
    return {
        "summary": new.title,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }


def create_event(service, new: NewEvent) -> dict:
    """Create the event in the account's primary calendar."""
    return service.events().insert(
        calendarId="primary", body=build_event_body(new)
    ).execute()
