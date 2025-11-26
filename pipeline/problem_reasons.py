from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Sequence

from .config import ComputationParams
from .utils import safe_div


def filter_fact_rows(
    fact_rows: Sequence[Dict[str, Any]],
    params: ComputationParams,
) -> List[Dict[str, Any]]:
    return [
        row
        for row in fact_rows
        if row["country"] == params.country
        and row["fasin"] == params.parent_asin
        and row.get("review_source") == 0
        and params.start_date <= row["review_date"] <= params.end_date
    ]


def build_problem_reasons(
    asin_structure: Sequence[Dict[str, Any]],
    fact_rows: Sequence[Dict[str, Any]],
    params: ComputationParams,
    tag_lookup: Dict[str, str] | None = None,
) -> List[Dict[str, Any]]:
    tag_lookup = tag_lookup or {}
    asin_lookup = {
        row["asin"]: row
        for row in asin_structure
        if row["problem_class"] in ("A", "B")
    }
    if not asin_lookup:
        return []

    asin_event_ids: Dict[str, set] = defaultdict(set)
    tag_event_ids: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
    tag_name_override: Dict[tuple[str, str], str] = {}

    for row in fact_rows:
        asin = row["asin"]
        if asin not in asin_lookup:
            continue
        review_id = row.get("review_id")
        if not review_id:
            continue
        tag_code = row.get("tag_code") or "UNLABELED"
        asin_event_ids[asin].add(review_id)
        tag_event_ids[asin][tag_code].add(review_id)
        tag_name = row.get("tag_name_cn") or tag_lookup.get(tag_code) or tag_code
        tag_name_override[(asin, tag_code)] = tag_name

    results: List[Dict[str, Any]] = []
    for asin, asin_data in asin_lookup.items():
        total_events = len(asin_event_ids.get(asin, set()))
        units_returned = asin_data["units_returned"]
        text_coverage = safe_div(total_events, units_returned)
        reason_confidence = _infer_confidence(total_events, text_coverage, params)
        can_deep_dive = reason_confidence in ("high", "medium")
        reason_stats = _build_reason_stats(
            asin, tag_event_ids.get(asin, {}), total_events, tag_lookup, tag_name_override
        )
        selected_reasons = _select_reasons(
            reason_stats,
            can_deep_dive,
            params,
        )
        coverage_reached = sum(item["event_coverage"] for item in selected_reasons)

        results.append(
            {
                "country": asin_data["country"],
                "fasin": asin_data["fasin"],
                "asin": asin,
                "start_date": asin_data["start_date"],
                "end_date": asin_data["end_date"],
                "problem_class": asin_data["problem_class"],
                "problem_class_label_cn": asin_data["problem_class_label_cn"],
                "total_events": total_events,
                "units_returned": units_returned,
                "text_coverage": text_coverage,
                "reason_confidence_level": reason_confidence,
                "can_deep_dive_reasons": can_deep_dive,
                "core_reasons": selected_reasons,
                "coverage_threshold": params.reason_selection.coverage_threshold,
                "coverage_reached": coverage_reached,
            }
        )

    order = {row["asin"]: idx for idx, row in enumerate(asin_structure)}
    results.sort(key=lambda item: order.get(item["asin"], 0))
    return results


def _build_reason_stats(
    asin: str,
    tag_records: Dict[str, set],
    total_events: int,
    tag_lookup: Dict[str, str],
    tag_name_override: Dict[tuple[str, str], str],
) -> List[Dict[str, Any]]:
    stats: List[Dict[str, Any]] = []
    for tag_code, review_ids in tag_records.items():
        event_count = len(review_ids)
        event_coverage = safe_div(event_count, total_events) if total_events else 0.0
        stats.append(
            {
                "tag_code": tag_code,
                "tag_name_cn": tag_name_override.get((asin, tag_code))
                or tag_lookup.get(tag_code)
                or tag_code,
                "event_count": event_count,
                "event_coverage": event_coverage,
            }
        )
    stats.sort(
        key=lambda item: (
            -item["event_count"],
            -item["event_coverage"],
            item["tag_code"],
        )
    )
    return stats


def _select_reasons(
    reason_stats: Sequence[Dict[str, Any]],
    can_deep_dive: bool,
    params: ComputationParams,
) -> List[Dict[str, Any]]:
    if not reason_stats:
        return []
    selection: List[Dict[str, Any]] = []
    coverage_threshold = params.reason_selection.coverage_threshold
    if can_deep_dive:
        coverage_sum = 0.0
        for item in reason_stats:
            selection.append({**item, "is_primary": len(selection) == 0})
            coverage_sum += item["event_coverage"]
            if coverage_sum >= coverage_threshold:
                break
            if len(selection) >= params.reason_selection.max_reasons_when_confident:
                break
        if not selection:
            selection.append({**reason_stats[0], "is_primary": True})
    else:
        limit = max(1, params.reason_selection.max_reasons_when_low_confidence)
        for item in reason_stats[:limit]:
            selection.append({**item, "is_primary": len(selection) == 0})
    return selection


def _infer_confidence(
    total_events: int,
    text_coverage: float,
    params: ComputationParams,
) -> str:
    thresholds = params.reason_thresholds
    if (
        total_events >= thresholds.high_min_samples
        and text_coverage >= thresholds.high_min_coverage
    ):
        return "high"
    if (
        total_events >= thresholds.medium_min_samples
        and text_coverage >= thresholds.medium_min_coverage
    ):
        return "medium"
    return "low"