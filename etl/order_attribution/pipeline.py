from __future__ import annotations

import argparse
import logging
from datetime import date as dt_date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ..shared.calculator import format_date, parse_date
from ..shared.utils import write_table
from ..shared.doris_client import DorisClient
from .asin_structure import build_asin_structure
from .cli_utils import build_stage_parser, resolve_runtime
from .config import PipelineConfig
from .parent_summary import calculate_parent_summary
from .problem_asin_listing import build_problem_asin_listing
from .problem_reasons import build_problem_reasons
from .reason_explanations import build_reason_explanations

LOGGER = logging.getLogger("etl.order_attribution.pipeline")
_write_table = write_table  # backward compatibility for run_* modules

INPUT_TABLES = [
    "view_return_snapshot",
    "view_return_orders_snapshot",
    "view_return_fact_details",
    "return_dim_tag",
    "view_bi_amz_asin_product_snapshot",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Order attribution view ETL pipeline")
    return parser.parse_args(argv)


def _read_table(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and len(payload) == 1:
        return list(payload.values())[0]  # assume {table: rows}
    if isinstance(payload, list):
        return payload
    return []


def _load_inputs(config: PipelineConfig) -> Dict[str, List[Dict]]:
    inputs: Dict[str, List[Dict]] = {}
    for table in INPUT_TABLES:
        table_path = config.paths.data_dir / f"{table}.json"
        inputs[table] = _read_table(table_path)
    return inputs


def _select_bi_snapshot_rows_for_window(
    snapshot_rows: Iterable[Dict],
    *,
    adjust_date,
    window: Tuple,
    window_label: str,
) -> List[Dict]:
    adjust_d = parse_date(adjust_date)
    start_d, end_d = parse_date(window[0]), parse_date(window[1])

    if window_label == "before":
        best_before: Dict[str, Tuple[dt_date, Dict]] = {}
        for row in snapshot_rows:
            asin = row.get("asin")
            if not asin:
                continue
            try:
                snap_d = parse_date(row.get("snapshot_date"))
            except Exception:
                continue
            if snap_d > adjust_d:
                continue
            current = best_before.get(asin)
            if current is None or snap_d > current[0]:
                best_before[asin] = (snap_d, row)
        return [entry[1] for entry in best_before.values()]

    best_in_window: Dict[str, Tuple[int, dt_date, Dict]] = {}  # asin -> (delta_days, date, row)
    best_latest_after: Dict[str, Tuple[dt_date, Dict]] = {}
    best_latest_any: Dict[str, Tuple[dt_date, Dict]] = {}

    for row in snapshot_rows:
        asin = row.get("asin")
        if not asin:
            continue
        try:
            snap_d = parse_date(row.get("snapshot_date"))
        except Exception:
            continue

        if asin not in best_latest_any or snap_d > best_latest_any[asin][0]:
            best_latest_any[asin] = (snap_d, row)

        if snap_d >= adjust_d and (asin not in best_latest_after or snap_d > best_latest_after[asin][0]):
            best_latest_after[asin] = (snap_d, row)

        if snap_d < adjust_d or snap_d > end_d:
            continue
        delta = (snap_d - adjust_d).days
        current = best_in_window.get(asin)
        if current is None or delta < current[0] or (delta == current[0] and snap_d > current[1]):
            best_in_window[asin] = (delta, snap_d, row)

    results: List[Dict] = []
    for asin, latest_any in best_latest_any.items():
        if asin in best_in_window:
            results.append(best_in_window[asin][2])
        elif asin in best_latest_after:
            results.append(best_latest_after[asin][1])
        else:
            results.append(latest_any[1])
    return results


def _fetch_inputs_from_doris(
    *,
    config: PipelineConfig,
    windows: Dict[str, Tuple],
    country: str,
    fasin: str,
) -> Dict[str, List[Dict]]:
    starts = [window[0] for window in windows.values()]
    ends = [window[1] for window in windows.values()]
    min_start, max_end = min(starts), max(ends)
    start_str, end_str = format_date(min_start), format_date(max_end)
    bi_end_str = format_date(max(max_end, dt_date.today()))

    LOGGER.info(
        "Pulling source tables from Doris for %s/%s between %s and %s into %s",
        country,
        fasin,
        start_str,
        end_str,
        config.paths.data_dir,
    )
    with DorisClient(
        database=config.database,
        paths=config.paths,
        date_mode="purchase",
    ) as client:
        snapshot_rows = client.fetch_view_return_snapshot(
            country=country,
            fasin=fasin,
            start_date=start_str,
            end_date=end_str,
        )
        order_rows = client.fetch_view_return_orders_snapshot(
            country=country,
            fasin=fasin,
            start_date=start_str,
            end_date=end_str,
        )
        fact_rows = client.fetch_view_return_fact_details(
            country=country,
            fasin=fasin,
            start_date=start_str,
            end_date=end_str,
        )
        tag_dim_rows = client.fetch_return_dim_tag()
        bi_snapshot_rows = client.fetch_view_bi_amz_asin_product_snapshot(
            country=country,
            fasin=fasin,
            start_date=start_str,
            # Use the freshest snapshot available (up to today) so we still get data if snapshots lag the purchase window.
            end_date=bi_end_str,
        )

    return {
        "view_return_snapshot": snapshot_rows,
        "view_return_orders_snapshot": order_rows,
        "view_return_fact_details": fact_rows,
        "return_dim_tag": tag_dim_rows,
        "view_bi_amz_asin_product_snapshot": bi_snapshot_rows,
    }


def load_or_fetch_inputs(
    *,
    config: PipelineConfig,
    windows: Dict[str, Tuple],
    country: str,
    fasin: str,
) -> Dict[str, List[Dict]]:
    # Always fetch fresh data from Doris and overwrite local cache.
    return _fetch_inputs_from_doris(config=config, windows=windows, country=country, fasin=fasin)


def _run_window(
    *,
    window_label: str,
    window: Tuple,
    config: PipelineConfig,
    inputs: Dict[str, List[Dict]],
    country: str,
    fasin: str,
    adjust_date,
) -> Dict[str, List[Dict] | Dict]:
    snapshot_rows = inputs.get("view_return_snapshot", [])
    return_orders = inputs.get("view_return_orders_snapshot", [])
    fact_rows = inputs.get("view_return_fact_details", [])
    tag_dim = inputs.get("return_dim_tag", [])
    bi_snapshot_rows_all = inputs.get("view_bi_amz_asin_product_snapshot", [])
    bi_snapshot_rows = _select_bi_snapshot_rows_for_window(
        bi_snapshot_rows_all,
        adjust_date=adjust_date,
        window=window,
        window_label=window_label,
    )

    parent_summary = calculate_parent_summary(
        snapshot_rows=snapshot_rows,
        return_rows=return_orders,
        country=country,
        fasin=fasin,
        window=window,
        window_label=window_label,
    )

    asin_structure = build_asin_structure(
        snapshot_rows=snapshot_rows,
        return_rows=return_orders,
        country=country,
        fasin=fasin,
        window=window,
        window_label=window_label,
        parent_summary=parent_summary,
        thresholds=config.thresholds,
    )

    problem_reasons = build_problem_reasons(
        asin_structure=asin_structure,
        fact_rows=fact_rows,
        tag_dimension=tag_dim,
        thresholds=config.thresholds,
        country=country,
        fasin=fasin,
        window=window,
        window_label=window_label,
    )

    reason_explanations = build_reason_explanations(
        problem_reasons=problem_reasons,
        fact_rows=fact_rows,
    )

    problem_asin_listing = build_problem_asin_listing(
        problem_reasons=problem_reasons,
        snapshot_rows=bi_snapshot_rows,
        window_label=window_label,
        window=window,
    )

    return {
        "parent_summary": parent_summary,
        "asin_structure": asin_structure,
        "problem_asin_reasons": problem_reasons,
        "reason_explanations": reason_explanations,
        "problem_asin_listing": problem_asin_listing,
    }


def run_pipeline(args: argparse.Namespace | None = None) -> Dict[str, Dict[str, List[Dict] | Dict]]:
    if args is None:
        args = parse_args()
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, windows = resolve_runtime(args)
    adjust_date = windows.get("after", next(iter(windows.values())))[0]
    inputs = load_or_fetch_inputs(
        config=config,
        windows=windows,
        country=args.country,
        fasin=args.fasin,
    )
    outputs: Dict[str, Dict[str, List[Dict] | Dict]] = {}
    for label, window in windows.items():
        start_str, end_str = format_date(window[0]), format_date(window[1])
        LOGGER.info(
            "[%s] Running ETL for %s/%s between %s and %s",
            label,
            args.country,
            args.fasin,
            start_str,
            end_str,
        )
        window_outputs = _run_window(
            window_label=label,
            window=window,
            config=config,
            inputs=inputs,
            country=args.country,
            fasin=args.fasin,
            adjust_date=adjust_date,
        )
        outputs[label] = window_outputs
        for table_name, payload in window_outputs.items():
            filename = f"{table_name}_{label}.json"
            output_path = config.paths.output_dir / filename
            payload_key = f"{table_name}_{label}"
            write_table(output_path, table_name, payload, key_override=payload_key)
            LOGGER.info("[%s] Wrote %s to %s", label, table_name, output_path)
    return outputs


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
