from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

from ..order_attribution.asin_structure import build_asin_structure
from ..order_attribution.parent_summary import calculate_parent_summary
from ..order_attribution.problem_asin_listing import build_problem_asin_listing
from ..order_attribution.problem_reasons import build_problem_reasons
from ..order_attribution.reason_explanations import build_reason_explanations
from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .config import PipelineConfig
from .doris_client import DorisClient

LOGGER = logging.getLogger("etl.purchase_window.pipeline")
# Use a distinct label for single-window purchase-date outputs and filenames.
WINDOW_LABEL = "purchase_window"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Single-window purchase-date attribution ETL pipeline")
    return parser.parse_args(argv)


def _write_table(path: Path, table_name: str, records: Iterable[Dict] | Dict, *, key_override: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(records, dict):
        records = [records]
    payload_key = key_override or table_name
    payload = {payload_key: list(records)}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def run_pipeline(args: argparse.Namespace | None = None) -> Dict[str, object]:
    if args is None:
        args = parse_args()
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, start_date, end_date = resolve_runtime(args)
    start_str, end_str = format_window(start_date, end_date)
    window = (start_date, end_date)

    LOGGER.info(
        "Running purchase-window ETL for %s/%s between %s and %s",
        args.country,
        args.fasin,
        start_str,
        end_str,
    )

    with DorisClient(
        database=config.database,
        data_dir=config.paths.data_dir,
        output_dir=config.paths.output_dir,
    ) as client:
        snapshot_rows = client.fetch_view_return_snapshot(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        order_rows = client.fetch_view_return_orders_snapshot(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        fact_rows = client.fetch_view_return_fact_details(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        tag_dim_rows = client.fetch_return_dim_tag()
        bi_snapshot_rows = client.fetch_view_bi_amz_asin_product_snapshot(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )

    parent_summary = calculate_parent_summary(
        snapshot_rows=snapshot_rows,
        return_rows=order_rows,
        country=args.country,
        fasin=args.fasin,
        window=window,
        window_label=WINDOW_LABEL,
    )

    asin_structure = build_asin_structure(
        snapshot_rows=snapshot_rows,
        return_rows=order_rows,
        country=args.country,
        fasin=args.fasin,
        window=window,
        window_label=WINDOW_LABEL,
        parent_summary=parent_summary,
        thresholds=config.thresholds,
    )

    problem_reasons = build_problem_reasons(
        asin_structure=asin_structure,
        fact_rows=fact_rows,
        tag_dimension=tag_dim_rows,
        thresholds=config.thresholds,
        country=args.country,
        fasin=args.fasin,
        window=window,
        window_label=WINDOW_LABEL,
    )

    reason_explanations = build_reason_explanations(
        problem_reasons=problem_reasons,
        fact_rows=fact_rows,
    )

    problem_asin_listing = build_problem_asin_listing(
        problem_reasons=problem_reasons,
        snapshot_rows=bi_snapshot_rows,
        window_label=WINDOW_LABEL,
        window=window,
    )

    outputs = {
        "parent_summary": parent_summary,
        "asin_structure": asin_structure,
        "problem_asin_reasons": problem_reasons,
        "reason_explanations": reason_explanations,
        "problem_asin_listing": problem_asin_listing,
    }

    results: Dict[str, object] = {}
    for table_name, payload in outputs.items():
        filename = f"{table_name}_{WINDOW_LABEL}.json"
        output_path = config.paths.output_dir / filename
        payload_key = f"{table_name}_{WINDOW_LABEL}"
        _write_table(output_path, table_name, payload, key_override=payload_key)
        results[payload_key] = payload
        LOGGER.info("Wrote %s to %s", payload_key, output_path)

    return results


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
