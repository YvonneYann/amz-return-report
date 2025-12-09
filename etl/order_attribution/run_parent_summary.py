from __future__ import annotations

import argparse
import logging

from .cli_utils import build_stage_parser, format_window, resolve_runtime
from .parent_summary import calculate_parent_summary
from .pipeline import _write_table, load_or_fetch_inputs

LOGGER = logging.getLogger("etl.order_attribution.run_parent_summary")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_stage_parser("Order attribution - parent summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, (args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config, windows, return_lag_days = resolve_runtime(args)
    inputs = load_or_fetch_inputs(
        config=config,
        windows=windows,
        country=args.country,
        fasin=args.fasin,
    )
    for label, window in windows.items():
        start_str, end_str = format_window(window)
        LOGGER.info(
            "[%s] Parent summary for %s/%s between %s and %s (return_lag_days=%s)",
            label,
            args.country,
            args.fasin,
            start_str,
            end_str,
            return_lag_days,
        )
        summary = calculate_parent_summary(
            snapshot_rows=inputs.get("view_return_snapshot", []),
            return_rows=inputs.get("view_return_orders_snapshot", []),
            country=args.country,
            fasin=args.fasin,
            window=window,
            window_label=label,
            return_lag_days=return_lag_days,
        )
        output_path = config.paths.output_dir / f"parent_summary_{label}.json"
        _write_table(output_path, "parent_summary", summary, key_override=f"parent_summary_{label}")
        LOGGER.info("[%s] Wrote parent_summary to %s", label, output_path)


if __name__ == "__main__":
    main()
