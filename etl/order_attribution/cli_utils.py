from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

from ..calculator import format_date, parse_date
from .config import PipelineConfig, build_config

DEFAULT_PARAMS_PATH = Path(__file__).resolve().parents[2] / "config" / "order_attribution_run_params.json"


def build_stage_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--country", help="Marketplace country code, e.g. US")
    parser.add_argument("--fasin", help="Parent ASIN")
    parser.add_argument("--adjust-date", dest="adjust_date", help="Adjustment anchor date (YYYY-MM-DD)")
    parser.add_argument("--window-days", type=int, help="Comparison window days (default 90)")
    parser.add_argument("--return-lag-days", type=int, help="Max return lag days (default 35)")
    parser.add_argument("--purchase-start-date-before", dest="purchase_start_date_before", help="Manual pre window start")
    parser.add_argument("--purchase-end-date-before", dest="purchase_end_date_before", help="Manual pre window end")
    parser.add_argument("--purchase-start-date-after", dest="purchase_start_date_after", help="Manual post window start")
    parser.add_argument("--purchase-end-date-after", dest="purchase_end_date_after", help="Manual post window end")
    parser.add_argument("--data-dir", help="Optional override for template/order_attribution/input")
    parser.add_argument("--output-dir", help="Optional override for template/order_attribution/output")
    parser.add_argument("--env-file", help="Environment config file (YAML)")
    parser.add_argument("--thresholds-json", help="JSON string to override threshold config")
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
    # utf-8-sig allows reading files that include a BOM without raising JSONDecodeError
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _maybe_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return parse_date(value)
    except Exception:
        return None


def _normalize_thresholds(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"thresholds-json is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("thresholds-json must decode to an object")
        return parsed
    raise ValueError("threshold overrides must be a dict or JSON string")


def compute_windows(
    *,
    adjust_date: date,
    window_days: int,
    before_start: Any,
    before_end: Any,
    after_start: Any,
    after_end: Any,
) -> Dict[str, Tuple[date, date]]:
    base = parse_date(adjust_date)
    start_before = _maybe_date(before_start) or (base - timedelta(days=window_days))
    end_before = _maybe_date(before_end) or (base - timedelta(days=1))
    start_after = _maybe_date(after_start) or base
    end_after = _maybe_date(after_end) or (base + timedelta(days=window_days - 1))
    return {
        "before": (start_before, end_before),
        "after": (start_after, end_after),
    }


def resolve_runtime(args: argparse.Namespace) -> Tuple[PipelineConfig, Dict[str, Tuple[date, date]], int]:
    data_dir = Path(args.data_dir).resolve() if args.data_dir else None
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    env_file = Path(args.env_file).resolve() if args.env_file else None
    params_path = Path(args.params_file).resolve() if args.params_file else DEFAULT_PARAMS_PATH
    params = _load_params(params_path)

    args.country = args.country or params.get("country")
    args.fasin = args.fasin or params.get("fasin")
    if not args.country or not args.fasin:
        raise ValueError("country and fasin must be provided either via CLI arguments or params file")

    adjust_value = args.adjust_date or params.get("adjust_date")
    if not adjust_value:
        raise ValueError("adjust_date is required for order attribution view")
    adjust_date = parse_date(adjust_value)

    window_days = args.window_days or _coerce_int(params.get("window_days")) or 90
    return_lag_days = args.return_lag_days or _coerce_int(params.get("return_lag_days")) or 35

    thresholds_override = _normalize_thresholds(params.get("thresholds"))
    if args.thresholds_json:
        thresholds_override = _normalize_thresholds(args.thresholds_json)

    windows = compute_windows(
        adjust_date=adjust_date,
        window_days=window_days,
        before_start=args.purchase_start_date_before or params.get("purchase_start_date_before"),
        before_end=args.purchase_end_date_before or params.get("purchase_end_date_before"),
        after_start=args.purchase_start_date_after or params.get("purchase_start_date_after"),
        after_end=args.purchase_end_date_after or params.get("purchase_end_date_after"),
    )

    config = build_config(
        data_dir=data_dir,
        output_dir=output_dir,
        return_lag_days=return_lag_days,
        window_days=window_days,
        environment_path=env_file,
        threshold_overrides=thresholds_override,
    )
    return config, windows, return_lag_days


def format_window(window: Tuple[date, date]) -> Tuple[str, str]:
    start, end = window
    return format_date(start), format_date(end)
