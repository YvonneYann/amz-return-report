from __future__ import annotations

from datetime import date, datetime
from typing import Optional

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def parse_snapshot_date(value: str) -> date:
    """Parse snapshot dates that are stored without time information."""
    return datetime.strptime(value, DATE_FMT).date()


def parse_review_date(value: str) -> date:
    """Parse review/return timestamps, gracefully handling missing time parts."""
    for fmt in (DATETIME_FMT, DATE_FMT):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported review date format: {value}")


def ensure_date(value: Optional[date | str]) -> Optional[date]:
    if value is None or isinstance(value, date):
        return value
    return parse_snapshot_date(value)


def safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator