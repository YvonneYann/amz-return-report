from __future__ import annotations

from typing import Dict, Iterable, Tuple

from ..calculator import calc_rate, format_date, parse_date, round_float


def normalize_number(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _filter_snapshot(
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    window: Tuple,
):
    start, end = window
    start_d = parse_date(start)
    end_d = parse_date(end)
    for row in rows:
        if row.get("country") != country or row.get("fasin") != fasin:
            continue
        snapshot_date = parse_date(row.get("snapshot_date"))
        if snapshot_date < start_d or snapshot_date > end_d:
            continue
        yield row


def _filter_returns(
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    window: Tuple,
):
    start, end = window
    start_d = parse_date(start)
    end_d = parse_date(end)
    for row in rows:
        if row.get("country") != country or row.get("fasin") != fasin:
            continue
        purchase_date = parse_date(row.get("purchase_date"))
        if purchase_date < start_d or purchase_date > end_d:
            continue
        review_date = parse_date(row.get("review_date")) if row.get("review_date") else purchase_date
        if review_date < purchase_date:
            continue
        yield row


def calculate_parent_summary(
    *,
    snapshot_rows: Iterable[Dict],
    return_rows: Iterable[Dict],
    country: str,
    fasin: str,
    window: Tuple,
    window_label: str,
) -> Dict:
    start_fmt, end_fmt = format_date(window[0]), format_date(window[1])
    filtered_snapshot = list(
        _filter_snapshot(snapshot_rows, country=country, fasin=fasin, window=window)
    )
    filtered_returns = list(
        _filter_returns(
            return_rows,
            country=country,
            fasin=fasin,
            window=window,
        )
    )
    total_units_sold = sum(normalize_number(row.get("units_sold")) for row in filtered_snapshot)
    total_units_returned = sum(normalize_number(row.get("quantity") or row.get("units_returned")) for row in filtered_returns)
    summary = {
        "country": country,
        "fasin": fasin,
        "window_label": window_label,
        "start_date": start_fmt,
        "end_date": end_fmt,
        "units_sold": int(total_units_sold),
        "units_returned": int(total_units_returned),
        "return_rate": round_float(calc_rate(total_units_returned, total_units_sold)),
    }
    return summary
