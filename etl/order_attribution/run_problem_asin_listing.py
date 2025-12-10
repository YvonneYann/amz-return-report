from __future__ import annotations

import argparse
import logging

from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .pipeline import _write_table, load_or_fetch_inputs, _select_bi_snapshot_rows_for_window
from .problem_asin_listing import build_problem_asin_listing
from .problem_reasons import build_problem_reasons
from .asin_structure import build_asin_structure
from .parent_summary import calculate_parent_summary

LOGGER = logging.getLogger("etl.order_attribution.run_problem_asin_listing")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Order attribution - problem ASIN listing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
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
    for label, window in windows.items():
        start_str, end_str = format_window(window)
        LOGGER.info(
            "[%s] Problem ASIN listing for %s/%s between %s and %s",
            label,
            args.country,
            args.fasin,
            start_str,
            end_str,
        )
        parent_summary = calculate_parent_summary(
            snapshot_rows=inputs.get("view_return_snapshot", []),
            return_rows=inputs.get("view_return_orders_snapshot", []),
            country=args.country,
            fasin=args.fasin,
            window=window,
            window_label=label,
        )
        asin_structure = build_asin_structure(
            snapshot_rows=inputs.get("view_return_snapshot", []),
            return_rows=inputs.get("view_return_orders_snapshot", []),
            country=args.country,
            fasin=args.fasin,
            window=window,
            window_label=label,
            parent_summary=parent_summary,
            thresholds=config.thresholds,
        )
        problem_reasons = build_problem_reasons(
            asin_structure=asin_structure,
            fact_rows=inputs.get("view_return_fact_details", []),
            tag_dimension=inputs.get("return_dim_tag", []),
            thresholds=config.thresholds,
            country=args.country,
            fasin=args.fasin,
            window=window,
            window_label=label,
        )
        bi_snapshot_rows = _select_bi_snapshot_rows_for_window(
            inputs.get("view_bi_amz_asin_product_snapshot", []),
            adjust_date=adjust_date,
            window=window,
            window_label=label,
        )
        listing = build_problem_asin_listing(
            problem_reasons=problem_reasons,
            snapshot_rows=bi_snapshot_rows,
            window_label=label,
            window=window,
        )
        output_path = config.paths.output_dir / f"problem_asin_listing_{label}.json"
        _write_table(output_path, "problem_asin_listing", listing, key_override=f"problem_asin_listing_{label}")
        LOGGER.info("[%s] Wrote problem_asin_listing to %s", label, output_path)


if __name__ == "__main__":
    main()
