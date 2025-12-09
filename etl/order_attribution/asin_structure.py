from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from ..calculator import calc_rate, calc_share, format_date, parse_date, round_float
from ..config import ThresholdConfig
from .parent_summary import normalize_number

PROBLEM_CLASS_LABELS = {
    "A": "主战场款",
    "B": "高退货问题款",
}


def _filter_snapshot(rows: Iterable[Dict], *, country: str, fasin: str, window: Tuple):
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
    return_lag_days: int,
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
        if (review_date - purchase_date).days > return_lag_days:
            continue
        yield row


def _classify_asin(
    *,
    return_rate: float,
    units_returned: float,
    sales_share: float,
    returns_share: float,
    thresholds: ThresholdConfig,
    parent_return_rate: float,
) -> Dict[str, bool | str | None]:
    r_high_b = max(parent_return_rate, thresholds.warn_return_rate) + thresholds.high_return_buffer
    is_high_return = return_rate >= r_high_b
    has_volume = units_returned >= thresholds.min_units_returned_b
    has_weight = (sales_share > thresholds.min_sales_share_b) or (returns_share > thresholds.min_returns_share_b)
    is_watchlist = is_high_return and has_volume and not has_weight
    is_problem_b = is_high_return and has_volume and has_weight and not is_watchlist
    is_problem_a = (sales_share >= thresholds.min_sales_share_a) or (
        returns_share >= thresholds.min_returns_share_a
    )

    problem_class = None
    if is_problem_b:
        problem_class = "B"
    elif is_problem_a:
        problem_class = "A"

    return {
        "problem_class": problem_class,
        "problem_class_label_cn": PROBLEM_CLASS_LABELS.get(problem_class, ""),
        "high_return_watchlist": bool(is_watchlist),
    }


def build_asin_structure(
    *,
    snapshot_rows: Iterable[Dict],
    return_rows: Iterable[Dict],
    country: str,
    fasin: str,
    window: Tuple,
    window_label: str,
    parent_summary: Dict,
    thresholds: ThresholdConfig,
    return_lag_days: int,
) -> List[Dict]:
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
            return_lag_days=return_lag_days,
        )
    )

    sold_grouped: Dict[str, float] = {}
    for row in filtered_snapshot:
        asin = row.get("asin")
        if not asin:
            continue
        sold_grouped[asin] = sold_grouped.get(asin, 0.0) + normalize_number(row.get("units_sold"))

    return_grouped: Dict[str, float] = {}
    for row in filtered_returns:
        asin = row.get("asin")
        if not asin:
            continue
        return_grouped[asin] = return_grouped.get(asin, 0.0) + normalize_number(
            row.get("quantity") or row.get("units_returned")
        )

    total_units_sold = parent_summary.get("units_sold", 0) or 0
    total_units_returned = parent_summary.get("units_returned", 0) or 0
    parent_return_rate = parent_summary.get("return_rate", 0.0) or 0.0

    records: List[Dict] = []
    for asin, units_sold in sold_grouped.items():
        units_returned = return_grouped.get(asin, 0.0)
        return_rate = calc_rate(units_returned, units_sold)
        sales_share = calc_share(units_sold, total_units_sold)
        returns_share = calc_share(units_returned, total_units_returned)
        classification = _classify_asin(
            return_rate=return_rate,
            units_returned=units_returned,
            sales_share=sales_share,
            returns_share=returns_share,
            thresholds=thresholds,
            parent_return_rate=parent_return_rate,
        )
        record = {
            "country": country,
            "fasin": fasin,
            "asin": asin,
            "window_label": window_label,
            "start_date": start_fmt,
            "end_date": end_fmt,
            "units_sold": int(units_sold),
            "units_returned": int(units_returned),
            "return_rate": round_float(return_rate),
            "sales_share": round_float(sales_share),
            "returns_share": round_float(returns_share),
            **classification,
        }
        records.append(record)

    records.sort(key=lambda item: (item["returns_share"], item["units_returned"]), reverse=True)
    top_n = thresholds.top_asin_rows
    if top_n > 0:
        records = records[:top_n]
    return records
