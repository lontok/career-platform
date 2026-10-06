from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.models import Experience

MIN_BAR_WIDTH = 1.0
MAX_TICKS = 6
TICK_STEPS = (1, 2, 5, 10, 20)
SITE_TIMEZONE = ZoneInfo("America/Los_Angeles")


@dataclass(frozen=True)
class TimelineRow:
    role_title: str
    organization: str
    anchor: str
    start_label: str
    end_label: str
    offset: float
    width: float
    featured: bool


@dataclass(frozen=True)
class TimelineTick:
    year: int
    offset: float


@dataclass(frozen=True)
class Timeline:
    rows: list[TimelineRow]
    ticks: list[TimelineTick]
    start_year: int
    end_year: int
    today_offset: float


def experience_anchor(experience: Experience) -> str:
    return f"role-{experience.id}"


def build_timeline(
    experiences: Sequence[Experience], *, today: date | None = None
) -> Timeline | None:
    """Place each role on a shared year axis, as percentages of the full span."""
    if not experiences:
        return None

    today = today or _today()
    start_year = min(experience.start_date.year for experience in experiences)
    end_year = max(_end_date(experience, today).year for experience in experiences) + 1
    axis_start = date(start_year, 1, 1)
    total_days = (date(end_year, 1, 1) - axis_start).days

    def percent(day: date) -> float:
        return (day - axis_start).days / total_days * 100

    rows = []
    for experience in experiences:
        offset = percent(experience.start_date)
        width = percent(_end_date(experience, today)) - offset
        rows.append(
            TimelineRow(
                role_title=experience.role_title,
                organization=experience.organization,
                anchor=experience_anchor(experience),
                start_label=experience.start_date.strftime("%b %Y"),
                end_label=(
                    experience.end_date.strftime("%b %Y")
                    if experience.end_date
                    else "Present"
                ),
                offset=offset,
                width=max(width, MIN_BAR_WIDTH),
                featured=bool(experience.featured),
            )
        )

    step = next(
        (step for step in TICK_STEPS if (end_year - start_year) / step <= MAX_TICKS),
        TICK_STEPS[-1],
    )
    first_tick = -(-start_year // step) * step
    ticks = [
        TimelineTick(year=year, offset=percent(date(year, 1, 1)))
        for year in range(first_tick, end_year, step)
    ]
    return Timeline(
        rows=rows,
        ticks=ticks,
        start_year=start_year,
        end_year=end_year,
        today_offset=percent(today),
    )


def _end_date(experience: Experience, today: date) -> date:
    return experience.end_date or today


def _today() -> date:
    return datetime.now(SITE_TIMEZONE).date()
