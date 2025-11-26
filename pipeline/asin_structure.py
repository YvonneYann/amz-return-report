from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Sequence

from .config import ComputationParams
from .utils import safe_div

PROBLEM_CLASS_LABEL = {
    "A": "主战场款",
    "B": "高退货问题款",
}


def build_asin_structure(
    snapshots: Sequence[Dict[str, Any]],
    parent_summary: Dict[str, Any],
    params: ComputationParams,
) -> List[Dict[str, Any]]:
    asin_agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"units_sold": 0, "units_returned": 0})
    for row in snapshots:
        bucket = asin_agg[row["asin"]]
        bucket["units_sold"] += row["units_sold"]
        bucket["units_returned"] += row["units_returned"]

    total_sold = parent_summary["units_sold"]
    total_returned = parent_summary["units_returned"]
    parent_rate = parent_summary["return_rate"]
    high_return_threshold = params.high_return_rate_threshold(parent_rate)

    structures: List[Dict[str, Any]] = []
    for asin, agg in asin_agg.items():
        units_sold = agg["units_sold"]
        units_returned = agg["units_returned"]
        if units_sold == 0 and units_returned == 0:
            continue
        return_rate = safe_div(units_returned, units_sold) if units_sold else 0.0
        sales_share = safe_div(units_sold, total_sold)
        returns_share = safe_div(units_returned, total_returned)
        is_main = (
            sales_share >= params.min_main_sales_share
            and returns_share >= params.min_main_returns_share
        )
        meets_rate = return_rate >= high_return_threshold
        meets_units = units_returned >= params.min_problem_units_returned
        meets_share = (
            sales_share > params.min_problem_share
            or returns_share > params.min_problem_share
        )
        problem_class = None
        if is_main:
            problem_class = "A"
        elif meets_rate and meets_units and meets_share:
            problem_class = "B"

        watchlist = (
            meets_rate
            and meets_units
            and not meets_share
            and sales_share <= params.problem_watchlist_share_max
            and returns_share <= params.problem_watchlist_share_max
        )

        structures.append(
            {
                "country": parent_summary["country"],
                "fasin": parent_summary["fasin"],
                "asin": asin,
                "start_date": parent_summary["start_date"],
                "end_date": parent_summary["end_date"],
                "units_sold": units_sold,
                "units_returned": units_returned,
                "return_rate": return_rate,
                "sales_share": sales_share,
                "returns_share": returns_share,
                "problem_class": problem_class,
                "problem_class_label_cn": PROBLEM_CLASS_LABEL.get(problem_class, "无"),
                "high_return_watchlist": watchlist,
            }
        )

    structures.sort(
        key=lambda item: (
            -item["returns_share"],
            -item["units_returned"],
            item["asin"],
        )
    )

    return _apply_asin_limit(structures, params.top_asin_limit)


def _apply_asin_limit(rows: List[Dict[str, Any]], limit: int | None) -> List[Dict[str, Any]]:
    if limit is None or limit <= 0 or limit >= len(rows):
        return rows
    selected = rows[:limit]
    included = {row["asin"] for row in selected}
    for row in rows[limit:]:
        needs_whitelist = (
            row["problem_class"] in ("A", "B") or row["high_return_watchlist"]
        )
        if needs_whitelist and row["asin"] not in included:
            selected.append(row)
            included.add(row["asin"])
    return selected