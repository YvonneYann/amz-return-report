from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..shared.calculator import parse_date, format_date


def _unwrap_problem_rows(raw: object) -> List[Dict[str, Any]]:
    if isinstance(raw, dict):
        payload = raw.get("problem_asin_reasons")
        return list(payload) if isinstance(payload, list) else []
    if isinstance(raw, list):
        return raw
    return []


def _unwrap_snapshot_rows(raw: object) -> List[Dict[str, Any]]:
    if isinstance(raw, dict):
        payload = raw.get("view_bi_amz_asin_product_snapshot")
        return list(payload) if isinstance(payload, list) else []
    if isinstance(raw, list):
        return raw
    return []


def _parse_snapshot_date(value: Any) -> Optional[date]:
    if value in {None, ""}:
        return None
    try:
        return parse_date(value)
    except Exception:
        return None


def _build_asin_filters(problem_rows: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    filters: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for row in problem_rows:
        asin = row.get("asin")
        if not asin:
            continue
        if asin not in filters:
            filters[asin] = {"country": row.get("country"), "fasin": row.get("fasin")}
            order.append(asin)
            continue
        if not filters[asin].get("country") and row.get("country"):
            filters[asin]["country"] = row.get("country")
        if not filters[asin].get("fasin") and row.get("fasin"):
            filters[asin]["fasin"] = row.get("fasin")
    return filters, order


def _matches_filters(row: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    if filters.get("country") and row.get("country") and row["country"] != filters["country"]:
        return False
    if filters.get("fasin") and row.get("fasin") and row["fasin"] != filters["fasin"]:
        return False
    return True


def _date_key(value: Any) -> Tuple[int, object]:
    parsed = _parse_snapshot_date(value)
    if parsed:
        return (1, parsed)
    return (0, str(value) if value is not None else "")


def build_problem_asin_listing(
    *,
    problem_reasons: object,
    snapshot_rows: object,
    window_label: str,
    window: Tuple,
) -> List[Dict[str, Any]]:
    """
    Filter view_bi_amz_asin_product_snapshot rows by problem ASINs and keep only the latest snapshot per ASIN.
    """
    problem_rows = _unwrap_problem_rows(problem_reasons)
    snapshot_list = _unwrap_snapshot_rows(snapshot_rows)
    asin_filters, asin_order = _build_asin_filters(problem_rows)
    if not asin_filters or not snapshot_list:
        return []

    best_date_key: Dict[str, Tuple[int, object]] = {}
    rows_by_asin: Dict[str, List[Dict[str, Any]]] = {}

    for row in snapshot_list:
        asin = row.get("asin")
        if not asin or asin not in asin_filters:
            continue
        filters = asin_filters[asin]
        if not _matches_filters(row, filters):
            continue
        key = _date_key(row.get("snapshot_date"))
        current_best = best_date_key.get(asin)
        if current_best is None or key > current_best:
            best_date_key[asin] = key
            rows_by_asin[asin] = [row]
        elif key == current_best:
            rows_by_asin[asin].append(row)

    results: List[Dict[str, Any]] = []
    for asin in asin_order:
        if asin in rows_by_asin:
            results.extend(rows_by_asin[asin])
    # Tag window info for downstream comparison
    start_str, end_str = format_date(window[0]), format_date(window[1])
    annotated: List[Dict[str, Any]] = []
    for row in results:
        new_row = dict(row)
        new_row["window_label"] = window_label
        new_row["start_date"] = start_str
        new_row["end_date"] = end_str
        annotated.append(new_row)
    return annotated
