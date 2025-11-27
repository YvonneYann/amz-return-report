from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Tuple

from .calculator import format_date, resolve_window
from .config import BASE_DIR, PipelineConfig, build_config

DEFAULT_PARAMS_PATH = BASE_DIR / "config" / "run_params.json"


def build_stage_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--country", help="Marketplace country code, e.g. US")
    parser.add_argument("--fasin", help="Parent ASIN")
    parser.add_argument("--biz-date", dest="biz_date", help="Business date (YYYY-MM-DD)")
    parser.add_argument("--window-days", type=int, help="Analysis window length in days")
    parser.add_argument("--start-date", help="Override window start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Override window end date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", help="Optional override for template/input directory")
    parser.add_argument("--output-dir", help="Optional override for template/output directory")
    parser.add_argument("--env-file", help="Environment config file (YAML)")
    parser.add_argument(
        "--params-file",
        default=str(DEFAULT_PARAMS_PATH),
        help=f"Run parameter JSON (defaults to {DEFAULT_PARAMS_PATH})",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser


def _load_params(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_runtime(args: argparse.Namespace) -> Tuple[PipelineConfig, date, date]:
    data_dir = Path(args.data_dir).resolve() if args.data_dir else None
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    env_file = Path(args.env_file).resolve() if args.env_file else None
    config = build_config(data_dir=data_dir, output_dir=output_dir, environment_path=env_file)

    params_path = Path(args.params_file).resolve() if args.params_file else DEFAULT_PARAMS_PATH
    params = _load_params(params_path)

    args.country = args.country or params.get("country")
    args.fasin = args.fasin or params.get("fasin")
    if not args.country or not args.fasin:
        raise ValueError("country and fasin must be provided either via CLI arguments or params file")

    resolved_window_days = args.window_days or _coerce_int(params.get("window_days")) or config.default_window_days
    args.window_days = resolved_window_days

    biz_date_value = args.biz_date or params.get("biz_date") or date.today()
    start_override = args.start_date or params.get("start_date")
    end_override = args.end_date or params.get("end_date")

    start_date, end_date = resolve_window(
        start_date=start_override,
        end_date=end_override,
        biz_date=biz_date_value,
        window_days=resolved_window_days,
    )
    return config, start_date, end_date


def format_window(start_date: date, end_date: date) -> Tuple[str, str]:
    return format_date(start_date), format_date(end_date)
