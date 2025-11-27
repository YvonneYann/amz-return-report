from __future__ import annotations

import logging
from typing import Dict, List

from .asin_structure import build_asin_structure
from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .doris_client import DorisClient
from .parent_summary import calculate_parent_summary

LOGGER = logging.getLogger("etl.run_asin_structure")


def run(args=None) -> List[Dict[str, object]]:
    parser = build_stage_parser("Run ASIN structure stage")
    parsed_args = parser.parse_args(args)
    logging.basicConfig(
        level=getattr(logging, (parsed_args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, start_date, end_date = resolve_runtime(parsed_args)
    start_str, end_str = format_window(start_date, end_date)
    LOGGER.info("ASIN structure window: %s ~ %s", start_str, end_str)

    with DorisClient(config.database, config.paths) as client:
        snapshot_rows = client.fetch_view_return_snapshot(
            country=parsed_args.country,
            fasin=parsed_args.fasin,
            start_date=start_str,
            end_date=end_str,
        )
        parent_summary = calculate_parent_summary(
            snapshot_rows,
            country=parsed_args.country,
            fasin=parsed_args.fasin,
            start_date=start_date,
            end_date=end_date,
        )
        asin_structure = build_asin_structure(
            snapshot_rows,
            country=parsed_args.country,
            fasin=parsed_args.fasin,
            start_date=start_date,
            end_date=end_date,
            parent_summary=parent_summary,
            thresholds=config.thresholds,
        )
        output_path = client.write_json("asin_structure", asin_structure)
        LOGGER.info("asin_structure written to %s", output_path)
    return asin_structure


def main() -> None:
    run()


if __name__ == "__main__":
    main()
