"""Tests for the GUI-free logic (no Google access, no GTK)."""

import datetime as dt
import unittest
from unittest.mock import MagicMock

from calendar_widget.agenda import group_by_day
from calendar_widget.calendar_api import build_event_body, create_event, fetch_events
from calendar_widget.models import Event, NewEvent


def local(year, month, day, hour=0, minute=0):
    return dt.datetime(year, month, day, hour, minute).astimezone()


class GroupByDayTest(unittest.TestCase):
    def test_groups_sorts_and_ignores_out_of_range(self):
        first = dt.date(2026, 11, 9)
        events = [
            Event(local(2026, 11, 9, 14), False, "B"),
            Event(local(2026, 11, 9, 9), False, "A"),
            Event(local(2026, 11, 9, 0), True, "All day"),
            Event(local(2026, 11, 11, 8), False, "Wednesday"),
            Event(local(2026, 11, 30, 8), False, "too far away"),
        ]
        result = group_by_day(first, 5, events)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0][0], first)
        self.assertEqual([e.title for e in result[0][1]], ["All day", "A", "B"])
        self.assertEqual([e.title for e in result[2][1]], ["Wednesday"])
        self.assertEqual(sum(len(items) for _, items in result), 4)

    def test_all_day_before_timed_event_at_same_start(self):
        first = dt.date(2026, 11, 9)
        events = [
            Event(local(2026, 11, 9, 0), False, "at midnight"),
            Event(local(2026, 11, 9, 0), True, "All day"),
        ]
        titles = [e.title for e in group_by_day(first, 1, events)[0][1]]
        self.assertEqual(titles, ["All day", "at midnight"])


class BuildEventBodyTest(unittest.TestCase):
    def test_all_day_end_is_next_day(self):
        body = build_event_body(NewEvent(
            "Holiday", dt.date(2026, 11, 9), dt.time(0), dt.time(0), True))
        self.assertEqual(body["start"], {"date": "2026-11-09"})
        self.assertEqual(body["end"], {"date": "2026-11-10"})
        self.assertEqual(body["summary"], "Holiday")

    def test_timed_event_has_utc_offset(self):
        body = build_event_body(NewEvent(
            "Meeting", dt.date(2026, 11, 9), dt.time(10, 0), dt.time(11, 30), False))
        start = dt.datetime.fromisoformat(body["start"]["dateTime"])
        end = dt.datetime.fromisoformat(body["end"]["dateTime"])
        self.assertIsNotNone(start.tzinfo)
        self.assertEqual(start.replace(tzinfo=None), dt.datetime(2026, 11, 9, 10, 0))
        self.assertEqual(end - start, dt.timedelta(hours=1, minutes=30))
        self.assertNotIn("timeZone", body["start"])

    def test_end_before_start_becomes_one_hour(self):
        body = build_event_body(NewEvent(
            "Backwards", dt.date(2026, 11, 9), dt.time(15, 0), dt.time(14, 0), False))
        start = dt.datetime.fromisoformat(body["start"]["dateTime"])
        end = dt.datetime.fromisoformat(body["end"]["dateTime"])
        self.assertEqual(end - start, dt.timedelta(hours=1))


class ServiceCallsTest(unittest.TestCase):
    @staticmethod
    def fake_service(calendars, events_execute):
        service = MagicMock()
        service.calendarList.return_value.list.return_value.execute.return_value = {
            "items": calendars}
        service.events.return_value.list.return_value.execute.side_effect = events_execute
        return service

    def test_fetch_events_parses_timed_and_all_day(self):
        service = self.fake_service(
            [{"id": "a"}],
            [{"items": [
                {"summary": "Event", "start": {"dateTime": "2026-11-09T10:00:00+01:00"}},
                {"start": {"date": "2026-11-10"}},
            ]}],
        )
        first_day, events = fetch_events(service, days=5)

        self.assertEqual(first_day, dt.date.today())
        self.assertEqual([e.title for e in events], ["Event", "(no title)"])
        self.assertFalse(events[0].all_day)
        self.assertTrue(events[1].all_day)

    def test_fetch_events_raises_if_every_calendar_fails(self):
        service = self.fake_service(
            [{"id": "a"}, {"id": "b"}],
            [RuntimeError("403"), RuntimeError("403")],
        )
        with self.assertRaises(RuntimeError):
            fetch_events(service)

    def test_fetch_events_keeps_going_if_one_calendar_fails(self):
        service = self.fake_service(
            [{"id": "a"}, {"id": "b"}],
            [RuntimeError("broken"),
             {"items": [{"summary": "ok", "start": {"dateTime": "2026-11-09T09:00:00+01:00"}}]}],
        )
        _, events = fetch_events(service)
        self.assertEqual([e.title for e in events], ["ok"])

    def test_create_event_inserts_into_primary_calendar(self):
        service = MagicMock()
        new = NewEvent("Test", dt.date(2026, 11, 9), dt.time(9), dt.time(10), False)
        create_event(service, new)

        service.events.return_value.insert.assert_called_once()
        kwargs = service.events.return_value.insert.call_args.kwargs
        self.assertEqual(kwargs["calendarId"], "primary")
        self.assertEqual(kwargs["body"]["summary"], "Test")


if __name__ == "__main__":
    unittest.main()
