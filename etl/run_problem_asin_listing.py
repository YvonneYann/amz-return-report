from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .config import build_config
from .problem_asin_listing import build_problem_asin_listing

LOGGER = logging.getLogger("etl.run_problem_asin_listing")


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser("Build problem_asin_listing from cached JSON files")
    parser.add_argument(
        "--problem-file",
        help="Path to problem_asin_reasons.json (defaults to <output_dir>/problem_asin_reasons.json)",
    )
    parser.add_argument(
        "--snapshot-file",
        help="Path to view_bi_amz_asin_product_snapshot.json (defaults to <data_dir>/view_bi_amz_asin_product_snapshot.json)",
    )
    parser.add_argument("--data-dir", help="Directory containing input JSON files (defaults to template/input)")
    parser.add_argument("--output-dir", help="Directory to write outputs (defaults to template/output)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args(argv)


def run(args: List[str] | None = None) -> List[Dict[str, Any]]:
    parsed_args = parse_args(args)
    logging.basicConfig(
        level=getattr(logging, (parsed_args.log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    config = build_config(
        data_dir=Path(parsed_args.data_dir).resolve() if parsed_args.data_dir else None,
        output_dir=Path(parsed_args.output_dir).resolve() if parsed_args.output_dir else None,
    )

    problem_path = (
        Path(parsed_args.problem_file)
        if parsed_args.problem_file
        else config.paths.output_dir / "problem_asin_reasons.json"
    )
    snapshot_path = (
        Path(parsed_args.snapshot_file)
        if parsed_args.snapshot_file
        else config.paths.data_dir / "view_bi_amz_asin_product_snapshot.json"
    )

    if not problem_path.exists():
        raise FileNotFoundError(f"problem_asin_reasons file not found: {problem_path}")
    if not snapshot_path.exists():
        raise FileNotFoundError(f"view_bi_amz_asin_product_snapshot file not found: {snapshot_path}")

    problem_data = _load_json(problem_path)
    snapshot_data = _load_json(snapshot_path)

    listings = build_problem_asin_listing(
        problem_reasons=problem_data,
        snapshot_rows=snapshot_data,
    )
    output_path = config.paths.output_dir / "problem_asin_listing.json"
    output_path.write_text(
        json.dumps({"problem_asin_listing": listings}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    LOGGER.info("Wrote %d listings to %s", len(listings), output_path)
    return listings


def main() -> None:
    run()


if __name__ == "__main__":
    main()
