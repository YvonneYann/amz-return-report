from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set

from .calculator import calc_share, format_date, parse_date, round_float
from .config import ThresholdConfig


def _build_tag_lookup(dim_rows: Iterable[Dict]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for row in dim_rows:
        code = row.get("tag_code")
        if not code:
            continue
        if code not in lookup:
            name = row.get("tag_name_cn") or row.get("tag_name") or ""
            lookup[code] = str(name)
    return lookup


def _filter_fact_rows(
    rows: Iterable[Dict],
    *,
    country: str,
    fasin: str,
    asin_whitelist: Set[str],
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
        if row.get("review_source") not in {0, 1, "0", "1"}:
            continue
        asin = row.get("asin")
        if asin not in asin_whitelist:
            continue
        review_date = parse_date(row.get("review_date"))
        if review_date < start or review_date > end:
            continue
        yield row


def _assess_confidence(
    *,
    sample_count: int,
    text_coverage: float,
    thresholds: ThresholdConfig,
) -> Dict[str, str | bool]:
    if sample_count >= thresholds.text_sample_high and text_coverage >= thresholds.text_coverage_high:
        level = "high"
    elif sample_count >= thresholds.text_sample_medium and text_coverage >= thresholds.text_coverage_medium:
        level = "medium"
    else:
        level = "low"
    return {"reason_confidence_level": level, "can_deep_dive_reasons": level in {"high", "medium"}}


def _select_core_reasons(
    *,
    tag_counter: Dict[str, Set[str]],
    sample_count: int,
    tag_lookup: Dict[str, str],
    thresholds: ThresholdConfig,
    can_deep_dive: bool,
) -> tuple[list[dict], float]:
    if sample_count == 0 or not tag_counter:
        return [], 0.0
    ordered_tags = sorted(tag_counter.items(), key=lambda item: len(item[1]), reverse=True)
    selected: List[Dict] = []
    cumulative = 0.0
    # For low-confidence ASINs we only surface the top 2 tags as reference issues.
    max_reasons = 2 if not can_deep_dive else thresholds.max_core_reasons
    for idx, (tag_code, review_ids) in enumerate(ordered_tags):
        event_count = len(review_ids)
        if event_count == 0:
            continue
        coverage = calc_share(event_count, sample_count)
        reason = {
            "tag_code": tag_code,
            "tag_name_cn": tag_lookup.get(tag_code, ""),
            "event_count": event_count,
            "event_coverage": round_float(coverage),
            "is_primary": idx == 0,
        }
        selected.append(reason)
        cumulative += coverage
        if not can_deep_dive:
            if len(selected) >= max_reasons:
                break
            continue
        if len(selected) >= max_reasons:
            break
        if cumulative >= thresholds.coverage_threshold and len(selected) >= thresholds.min_core_reasons:
            break
    return selected, round_float(cumulative)


def build_problem_reasons(
    *,
    asin_structure: Iterable[Dict],
    fact_rows: Iterable[Dict],
    tag_dimension: Iterable[Dict],
    thresholds: ThresholdConfig,
    country: str,
    fasin: str,
    start_date,
    end_date,
) -> List[Dict]:
    start_fmt = format_date(start_date)
    end_fmt = format_date(end_date)
    problem_asins = [
        asin for asin in asin_structure if asin.get("problem_class") in {"A", "B"}
    ]
    asin_lookup = {record["asin"]: record for record in problem_asins if record.get("asin")}
    asin_whitelist = set(asin_lookup.keys())
    if not asin_whitelist:
        return []

    tag_lookup = _build_tag_lookup(tag_dimension)
    filtered_rows = list(
        _filter_fact_rows(
            fact_rows,
            country=country,
            fasin=fasin,
            asin_whitelist=asin_whitelist,
            start_date=start_fmt,
            end_date=end_fmt,
        )
    )

    asin_events: Dict[str, Dict[str, Set[str]]] = {}
    for row in filtered_rows:
        asin = row.get("asin")
        if asin not in asin_whitelist:
            continue
        asin_bucket = asin_events.setdefault(asin, {"reviews": set(), "tags": defaultdict(set)})
        review_id = row.get("review_id")
        if review_id:
            asin_bucket["reviews"].add(review_id)
            tag_code = row.get("tag_code")
            if tag_code:
                asin_bucket["tags"][tag_code].add(review_id)
                if tag_code not in tag_lookup and row.get("tag_name_cn"):
                    tag_lookup[tag_code] = row.get("tag_name_cn")

    results: List[Dict] = []
    for asin, asin_record in asin_lookup.items():
        bucket = asin_events.get(asin, {"reviews": set(), "tags": defaultdict(set)})
        sample_count = len(bucket["reviews"])
        units_returned = asin_record.get("units_returned", 0)
        text_coverage = calc_share(sample_count, units_returned)
        confidence = _assess_confidence(
            sample_count=sample_count,
            text_coverage=text_coverage,
            thresholds=thresholds,
        )
        core_reasons, coverage_reached = _select_core_reasons(
            tag_counter=bucket["tags"],
            sample_count=sample_count,
            tag_lookup=tag_lookup,
            thresholds=thresholds,
            can_deep_dive=confidence["can_deep_dive_reasons"],
        )
        result = {
            "country": country,
            "fasin": fasin,
            "asin": asin,
            "start_date": start_fmt,
            "end_date": end_fmt,
            "problem_class": asin_record.get("problem_class"),
            "problem_class_label_cn": asin_record.get("problem_class_label_cn", ""),
            "total_events": sample_count,
            "units_returned": int(units_returned),
            "text_coverage": round_float(text_coverage),
            "core_reasons": core_reasons,
            "coverage_threshold": thresholds.coverage_threshold,
            "coverage_reached": coverage_reached,
            **confidence,
        }
        results.append(result)

    return results
