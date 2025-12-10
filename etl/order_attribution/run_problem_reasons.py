from __future__ import annotations

import argparse
import logging

from .asin_structure import build_asin_structure
from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .parent_summary import calculate_parent_summary
from .pipeline import _write_table, load_or_fetch_inputs
from .problem_reasons import build_problem_reasons

LOGGER = logging.getLogger("etl.order_attribution.run_problem_reasons")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Order attribution - problem reasons")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, windows = resolve_runtime(args)
    inputs = load_or_fetch_inputs(
        config=config,
        windows=windows,
        country=args.country,
        fasin=args.fasin,
    )
    for label, window in windows.items():
        start_str, end_str = format_window(window)
        LOGGER.info(
            "[%s] Problem reasons for %s/%s between %s and %s",
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
        output_path = config.paths.output_dir / f"problem_asin_reasons_{label}.json"
        _write_table(
            output_path,
            "problem_asin_reasons",
            problem_reasons,
            key_override=f"problem_asin_reasons_{label}",
        )
        LOGGER.info("[%s] Wrote problem_asin_reasons to %s", label, output_path)


if __name__ == "__main__":
    main()
