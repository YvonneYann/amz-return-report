from __future__ import annotations

from typing import Dict, Iterable, List

from .calculator import calc_rate, calc_share, format_date, round_float
from .config import ThresholdConfig
from .parent_summary import filter_snapshot, normalize_number

PROBLEM_CLASS_LABELS = {
    "A": "\u4e3b\u6218\u573a\u6b3e",
    "B": "\u9ad8\u9000\u8d27\u95ee\u9898\u6b3e",
}


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
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    start_date,
    end_date,
    parent_summary: Dict,
    thresholds: ThresholdConfig,
) -> List[Dict]:
    start_fmt = format_date(start_date)
    end_fmt = format_date(end_date)
    filtered_rows = list(
        filter_snapshot(
            rows,
            country=country,
            fasin=fasin,
            start_date=start_fmt,
            end_date=end_fmt,
        )
    )
    grouped: Dict[str, Dict[str, float]] = {}
    for row in filtered_rows:
        asin = row.get("asin")
        if not asin:
            continue
        asin_bucket = grouped.setdefault(asin, {"units_sold": 0.0, "units_returned": 0.0})
        asin_bucket["units_sold"] += normalize_number(row.get("units_sold"))
        asin_bucket["units_returned"] += normalize_number(row.get("units_returned"))

    total_units_sold = parent_summary.get("units_sold", 0) or 0
    total_units_returned = parent_summary.get("units_returned", 0) or 0
    parent_return_rate = parent_summary.get("return_rate", 0.0) or 0.0

    records: List[Dict] = []
    for asin, metrics in grouped.items():
        units_sold = metrics["units_sold"]
        units_returned = metrics["units_returned"]
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
