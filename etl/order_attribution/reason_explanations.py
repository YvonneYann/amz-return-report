from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ..shared.calculator import parse_date


def _unwrap_problem_rows(raw: object) -> List[Dict[str, Any]]:
    if isinstance(raw, dict):
        payload = raw.get("problem_asin_reasons")
        return list(payload) if isinstance(payload, list) else []
    if isinstance(raw, list):
        return raw
    return []


def _unwrap_fact_rows(raw: object) -> List[Dict[str, Any]]:
    if isinstance(raw, dict):
        payload = raw.get("view_return_fact_details")
        return list(payload) if isinstance(payload, list) else []
    if isinstance(raw, list):
        return raw
    return []


def _parse_optional_date(value: Any) -> Optional[date]:
    if value in {None, ""}:
        return None
    try:
        return parse_date(value)
    except Exception:
        return None


def _build_asin_filters(problem_rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    asin_filters: Dict[str, Dict[str, Any]] = {}
    for row in problem_rows:
        asin = row.get("asin")
        core_reasons = row.get("core_reasons") or []
        tag_codes: Set[str] = {reason.get("tag_code") for reason in core_reasons if reason.get("tag_code")}
        if not asin or not tag_codes:
            continue
        bucket = asin_filters.setdefault(
            asin,
            {
                "tags": set(),
                "country": row.get("country"),
                "fasin": row.get("fasin"),
                "start_date": _parse_optional_date(row.get("start_date")),
                "end_date": _parse_optional_date(row.get("end_date")),
                "window_label": row.get("window_label"),
            },
        )
        bucket["tags"].update(tag_codes)
        if bucket.get("start_date") is None:
            bucket["start_date"] = _parse_optional_date(row.get("start_date"))
        if bucket.get("end_date") is None:
            bucket["end_date"] = _parse_optional_date(row.get("end_date"))
        if bucket.get("window_label") is None and row.get("window_label"):
            bucket["window_label"] = row.get("window_label")
    return asin_filters


def _in_purchase_range(purchase_date: Any, start_date: Optional[date], end_date: Optional[date]) -> bool:
    parsed = _parse_optional_date(purchase_date)
    if parsed is None:
        return True
    if start_date and parsed < start_date:
        return False
    if end_date and parsed > end_date:
        return False
    return True


def build_reason_explanations(
    *,
    problem_reasons: object,
    fact_rows: object,
) -> List[Dict[str, Any]]:
    problem_rows = _unwrap_problem_rows(problem_reasons)
    fact_rows_list = _unwrap_fact_rows(fact_rows)
    asin_filters = _build_asin_filters(problem_rows)
    if not asin_filters or not fact_rows_list:
        return []

    filtered: List[Dict[str, Any]] = []
    for row in fact_rows_list:
        asin = row.get("asin")
        tag_code = row.get("tag_code")
        if not asin or asin not in asin_filters or not tag_code:
            continue
        filters = asin_filters[asin]
        if tag_code not in filters["tags"]:
            continue
        if filters.get("country") and row.get("country") and row["country"] != filters["country"]:
            continue
        if filters.get("fasin") and row.get("fasin") and row["fasin"] != filters["fasin"]:
            continue
        if not _in_purchase_range(row.get("purchase_date"), filters.get("start_date"), filters.get("end_date")):
            continue
        enriched = dict(row)
        if filters.get("window_label"):
            enriched["window_label"] = filters["window_label"]
        if filters.get("start_date"):
            enriched["start_date"] = filters["start_date"].isoformat()
        if filters.get("end_date"):
            enriched["end_date"] = filters["end_date"].isoformat()
        filtered.append(enriched)
    return filtered
