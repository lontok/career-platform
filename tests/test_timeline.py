from __future__ import annotations

from datetime import date

from app.models import Experience
from app.services.timeline import build_timeline, describe_span


def _role(title: str, start: date, end: date | None, *, featured: bool = False):
    return Experience(
        id=hash(title) % 10_000,
        role_title=title,
        organization="Example Co",
        location="Los Angeles, CA",
        start_date=start,
        end_date=end,
        is_current=end is None,
        summary="",
        published=True,
        featured=featured,
        display_order=0,
    )


def test_build_timeline_positions_bars_on_a_shared_year_axis() -> None:
    roles = [
        _role("Current", date(2020, 1, 1), None, featured=True),
        _role("First", date(2010, 1, 1), date(2015, 1, 1)),
    ]

    timeline = build_timeline(roles, today=date(2025, 1, 1))

    assert timeline is not None
    assert (timeline.start_year, timeline.end_year) == (2010, 2026)
    current, first = timeline.rows
    assert first.offset == 0
    assert round(first.width, 1) == round(5 / 16 * 100, 1)
    assert round(current.offset, 1) == round(10 / 16 * 100, 1)
    assert current.featured is True
    assert current.end_label == "Present"
    assert first.start_label == "Jan 2010"
    assert [tick.year for tick in timeline.ticks] == [2010, 2015, 2020, 2025]
    assert timeline.ticks[0].offset == 0
    assert round(timeline.today_offset, 1) == round(15 / 16 * 100, 1)


def test_build_timeline_returns_none_without_roles() -> None:
    assert build_timeline([], today=date(2025, 1, 1)) is None


def test_build_timeline_keeps_short_roles_visible() -> None:
    roles = [
        _role("Long", date(1990, 1, 1), date(2020, 1, 1)),
        _role("Short", date(2000, 1, 1), date(2000, 1, 15)),
    ]

    timeline = build_timeline(roles, today=date(2025, 1, 1))

    assert timeline is not None
    assert min(row.width for row in timeline.rows) >= 1


def test_describe_span_counts_roles_and_years() -> None:
    roles = [
        _role("Current", date(2000, 3, 1), None),
        _role("Earlier", date(1998, 6, 1), date(2000, 2, 1)),
    ]

    assert describe_span(roles, today=date(2026, 10, 6)) == "2 roles across 28 years"
    assert describe_span(roles[:1], today=date(2000, 9, 1)) == "1 role across 1 year"
    assert describe_span([], today=date(2026, 10, 6)) == ""
