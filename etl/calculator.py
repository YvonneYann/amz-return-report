from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Tuple, Union

DateInput = Union[str, date, datetime]


def parse_date(value: DateInput) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        raise ValueError(f"Unsupported date value: {value!r}")
    value = value.strip()
    if not value:
        raise ValueError("Empty date string")
    lowered = value.lower()
    if lowered == "today":
        return date.today()
    if lowered == "yesterday":
        return date.today() - timedelta(days=1)
    if "T" in value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {value}")


def format_date(value: DateInput) -> str:
    return parse_date(value).strftime("%Y-%m-%d")


def resolve_window(
    *,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    biz_date: DateInput | None = None,
    window_days: int = 30,
) -> Tuple[date, date]:
    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
    else:
        end = parse_date(end_date or biz_date or date.today())
        start = end - timedelta(days=max(window_days - 1, 0))
    if start > end:
        raise ValueError("start_date cannot be later than end_date")
    return start, end


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def calc_share(part: float, total: float) -> float:
    return safe_divide(part, total, 0.0)


def calc_rate(numerator: float, denominator: float) -> float:
    return safe_divide(numerator, denominator, 0.0)


def round_float(value: float, digits: int = 4) -> float:
    return round(float(value), ndigits=digits)


def daterange(days: int) -> List[date]:
    today = date.today()
    return [today - timedelta(days=offset) for offset in range(days)]
