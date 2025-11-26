from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .config import ComputationParams
from .utils import safe_div


def filter_snapshot_rows(
    snapshot_rows: Sequence[Dict[str, Any]],
    params: ComputationParams,
) -> List[Dict[str, Any]]:
    return [
        row
        for row in snapshot_rows
        if row["country"] == params.country
        and row["fasin"] == params.parent_asin
        and params.start_date <= row["snapshot_date"] <= params.end_date
    ]


def build_parent_summary(
    filtered_snapshots: Sequence[Dict[str, Any]],
    params: ComputationParams,
) -> Dict[str, Any]:
    total_units_sold = sum(row["units_sold"] for row in filtered_snapshots)
    total_units_returned = sum(row["units_returned"] for row in filtered_snapshots)
    return {
        "country": params.country,
        "fasin": params.parent_asin,
        "start_date": params.start_date.isoformat(),
        "end_date": params.end_date.isoformat(),
        "units_sold": total_units_sold,
        "units_returned": total_units_returned,
        "return_rate": safe_div(total_units_returned, total_units_sold),
    }