from __future__ import annotations

from typing import Dict, Iterable

from .calculator import calc_rate, format_date, parse_date, round_float


def normalize_number(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def filter_snapshot(
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    start_date,
    end_date,
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    for row in rows:
        if row.get("country") != country:
            continue
        if row.get("fasin") != fasin:
            continue
        snapshot_date = parse_date(row.get("snapshot_date"))
        if snapshot_date < start or snapshot_date > end:
            continue
        yield row


def calculate_parent_summary(
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    start_date,
    end_date,
) -> Dict:
    start_fmt = format_date(start_date)
    end_fmt = format_date(end_date)
    filtered = list(
        filter_snapshot(
            rows,
            country=country,
            fasin=fasin,
            start_date=start_fmt,
            end_date=end_fmt,
        )
    )
    total_units_sold = sum(normalize_number(row.get("units_sold")) for row in filtered)
    total_units_returned = sum(normalize_number(row.get("units_returned")) for row in filtered)
    summary = {
        "country": country,
        "fasin": fasin,
        "start_date": start_fmt,
        "end_date": end_fmt,
        "units_sold": int(total_units_sold),
        "units_returned": int(total_units_returned),
        "return_rate": round_float(calc_rate(total_units_returned, total_units_sold)),
    }
    return summary
