from __future__ import annotations

import argparse
import logging
from typing import Dict

from .asin_structure import build_asin_structure
from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .doris_client import DorisClient
from .parent_summary import calculate_parent_summary
from .problem_reasons import build_problem_reasons
from .reason_explanations import build_reason_explanations

LOGGER = logging.getLogger("etl.pipeline")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Amazon return analysis ETL pipeline")
    return parser.parse_args(argv)



def run_pipeline(args: argparse.Namespace | None = None) -> Dict[str, object]:
    if args is None:
        args = parse_args()
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, start_date, end_date = resolve_runtime(args)
    LOGGER.info("Running ETL for %s/%s between %s and %s", args.country, args.fasin, start_date, end_date)

    start_str, end_str = format_window(start_date, end_date)

    with DorisClient(config.database, config.paths) as client:
        snapshot_rows = client.fetch_view_return_snapshot(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        parent_summary = calculate_parent_summary(
            snapshot_rows,
            country=args.country,
            fasin=args.fasin,
            start_date=start_date,
            end_date=end_date,
        )
        LOGGER.info(
            "Parent summary: units_sold=%s units_returned=%s return_rate=%.4f",
            parent_summary.get("units_sold"),
            parent_summary.get("units_returned"),
            parent_summary.get("return_rate"),
        )

        asin_structure = build_asin_structure(
            snapshot_rows,
            country=args.country,
            fasin=args.fasin,
            start_date=start_date,
            end_date=end_date,
            parent_summary=parent_summary,
            thresholds=config.thresholds,
        )
        LOGGER.info("Identified %d ASIN rows", len(asin_structure))

        fact_rows = client.fetch_view_return_fact_details(
            country=args.country,
            fasin=args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        tag_dim = client.fetch_return_dim_tag()
        problem_reasons = build_problem_reasons(
            asin_structure=asin_structure,
            fact_rows=fact_rows,
            tag_dimension=tag_dim,
            thresholds=config.thresholds,
            country=args.country,
            fasin=args.fasin,
            start_date=start_date,
            end_date=end_date,
        )
        LOGGER.info("Computed %d problem ASIN reason rows", len(problem_reasons))
        reason_explanations = build_reason_explanations(
            problem_reasons=problem_reasons,
            fact_rows=fact_rows,
        )
        LOGGER.info("Filtered %d reason explanation rows", len(reason_explanations))

        outputs = {
            "parent_summary": parent_summary,
            "asin_structure": asin_structure,
            "problem_asin_reasons": problem_reasons,
            "reason_explanations": reason_explanations,
        }
        for table_name, payload in outputs.items():
            output_path = client.write_json(table_name, payload)
            LOGGER.info("Wrote %s to %s", table_name, output_path)

    return outputs


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()

