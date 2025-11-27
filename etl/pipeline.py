from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path
from typing import Dict

from .asin_structure import build_asin_structure
from .calculator import format_date, resolve_window
from .config import PipelineConfig, build_config
from .doris_client import DorisClient
from .parent_summary import calculate_parent_summary
from .problem_reasons import build_problem_reasons

LOGGER = logging.getLogger("etl.pipeline")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazon return analysis ETL pipeline")
    parser.add_argument("--country", required=True, help="Marketplace country code, e.g. US")
    parser.add_argument("--fasin", required=True, help="Parent ASIN")
    parser.add_argument("--biz-date", dest="biz_date", help="Business date (YYYY-MM-DD)")
    parser.add_argument("--window-days", type=int, help="Analysis window in days")
    parser.add_argument("--start-date", help="Override window start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Override window end date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", help="Optional override for template/input directory")
    parser.add_argument("--output-dir", help="Optional override for template/output directory")
    parser.add_argument("--env-file", help="Override environment config file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


def _build_runtime_config(args: argparse.Namespace) -> PipelineConfig:
    data_dir = Path(args.data_dir).resolve() if args.data_dir else None
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    env_file = Path(args.env_file).resolve() if args.env_file else None
    config = build_config(data_dir=data_dir, output_dir=output_dir, environment_path=env_file)
    return config


def run_pipeline(args: argparse.Namespace | None = None) -> Dict[str, object]:
    if args is None:
        args = parse_args()
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = _build_runtime_config(args)
    window_days = args.window_days or config.default_window_days
    biz_date_value = args.biz_date or date.today()
    start_date, end_date = resolve_window(
        start_date=args.start_date,
        end_date=args.end_date,
        biz_date=biz_date_value,
        window_days=window_days,
    )
    LOGGER.info("Running ETL for %s/%s between %s and %s", args.country, args.fasin, start_date, end_date)

    start_str = format_date(start_date)
    end_str = format_date(end_date)

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

        outputs = {
            "parent_summary": parent_summary,
            "asin_structure": asin_structure,
            "problem_asin_reasons": problem_reasons,
        }
        for table_name, payload in outputs.items():
            output_path = client.write_json(table_name, payload)
            LOGGER.info("Wrote %s to %s", table_name, output_path)

    return outputs


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
