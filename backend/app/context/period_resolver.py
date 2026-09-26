import calendar
import re
from datetime import date, timedelta


MONTHS = {
    name.lower(): index
    for index, name in enumerate(calendar.month_name)
    if name
}
MONTHS.update(
    {
        name.lower(): index
        for index, name in enumerate(calendar.month_abbr)
        if name
    }
)


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    absolute = (year * 12 + (month - 1)) + offset
    return absolute // 12, (absolute % 12) + 1


def _quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    start_month = ((quarter - 1) * 3) + 1
    end_month = start_month + 2
    start = date(year, start_month, 1)
    end = date(
        year,
        end_month,
        calendar.monthrange(year, end_month)[1],
    )
    return start, end


def _result(
    label: str | None = None,
    source_text: str | None = None,
    start: date | None = None,
    end: date | None = None,
    matched: bool = False,
) -> dict:
    return {
        "matched": matched,
        "label": label,
        "source_text": source_text,
        "start_date": _iso(start),
        "end_date": _iso(end),
    }


def resolve_period(
    question: str,
    today: date | None = None,
) -> dict:
    """Resolve common date expressions without using an LLM."""
    today = today or date.today()
    text = " ".join(question.lower().split())

    range_patterns = [
        r"\bfrom\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})\b",
        r"\bbetween\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})\b",
    ]
    for pattern in range_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                start = date.fromisoformat(match.group(1))
                end = date.fromisoformat(match.group(2))
            except ValueError:
                return _result()
            if start > end:
                start, end = end, start
            return _result(
                label="explicit_range",
                source_text=match.group(0),
                start=start,
                end=end,
                matched=True,
            )

    named_days = {
        "today": (today, today),
        "yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        "tomorrow": (today + timedelta(days=1), today + timedelta(days=1)),
    }
    for phrase, (start, end) in named_days.items():
        if re.search(rf"\b{phrase}\b", text):
            return _result(phrase, phrase, start, end, True)

    week_match = re.search(r"\b(this|last|next)\s+week\b", text)
    if week_match:
        direction = week_match.group(1)
        monday = today - timedelta(days=today.weekday())
        offset = {"last": -7, "this": 0, "next": 7}[direction]
        start = monday + timedelta(days=offset)
        return _result(
            f"{direction}_week",
            week_match.group(0),
            start,
            start + timedelta(days=6),
            True,
        )

    month_match = re.search(r"\b(this|last|next)\s+month\b", text)
    if month_match:
        direction = month_match.group(1)
        year, month = _shift_month(
            today.year,
            today.month,
            {"last": -1, "this": 0, "next": 1}[direction],
        )
        start, end = _month_bounds(year, month)
        return _result(
            f"{direction}_month",
            month_match.group(0),
            start,
            end,
            True,
        )

    quarter_match = re.search(r"\b(this|last|next)\s+quarter\b", text)
    if quarter_match:
        direction = quarter_match.group(1)
        current_quarter = ((today.month - 1) // 3) + 1
        absolute = today.year * 4 + (current_quarter - 1)
        absolute += {"last": -1, "this": 0, "next": 1}[direction]
        year = absolute // 4
        quarter = (absolute % 4) + 1
        start, end = _quarter_bounds(year, quarter)
        return _result(
            f"{direction}_quarter",
            quarter_match.group(0),
            start,
            end,
            True,
        )

    year_match = re.search(r"\b(this|last|next)\s+year\b", text)
    if year_match:
        direction = year_match.group(1)
        year = today.year + {"last": -1, "this": 0, "next": 1}[direction]
        return _result(
            f"{direction}_year",
            year_match.group(0),
            date(year, 1, 1),
            date(year, 12, 31),
            True,
        )

    rolling = re.search(
        r"\blast\s+(\d{1,3})\s+(day|days|week|weeks|month|months)\b",
        text,
    )
    if rolling:
        count = max(1, min(int(rolling.group(1)), 366))
        unit = rolling.group(2)
        if unit.startswith("day"):
            start = today - timedelta(days=count - 1)
        elif unit.startswith("week"):
            start = today - timedelta(days=(count * 7) - 1)
        else:
            year, month = _shift_month(today.year, today.month, -count)
            last_day = calendar.monthrange(year, month)[1]
            start = date(year, month, min(today.day, last_day))
        return _result(
            f"last_{count}_{unit}",
            rolling.group(0),
            start,
            today,
            True,
        )

    month_names = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))
    named_month = re.search(
        rf"\b({month_names})(?:\s+(\d{{4}}))?\b",
        text,
    )
    if named_month:
        month = MONTHS[named_month.group(1)]
        year = int(named_month.group(2) or today.year)
        start, end = _month_bounds(year, month)
        return _result(
            "named_month",
            named_month.group(0),
            start,
            end,
            True,
        )

    explicit_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if explicit_date:
        try:
            value = date.fromisoformat(explicit_date.group(1))
        except ValueError:
            return _result()
        return _result(
            "explicit_date",
            explicit_date.group(0),
            value,
            value,
            True,
        )

    return _result()
