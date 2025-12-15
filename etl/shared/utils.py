from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Tuple

from .calculator import format_date, resolve_window
from .config_base import DEFAULT_ENV_PATH


# ---------- CLI/runtime helpers ----------
def build_single_window_parser(
    *,
    description: str,
    default_params_path: Path,
    data_help: str,
    output_help: str,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--country", help="Marketplace country code, e.g. US")
    parser.add_argument("--fasin", help="Parent ASIN")
    parser.add_argument("--biz-date", dest="biz_date", help="Business date (YYYY-MM-DD)")
    parser.add_argument("--window-days", type=int, help="Analysis window length in days")
    parser.add_argument("--start-date", help="Override window start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Override window end date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", help=data_help)
    parser.add_argument("--output-dir", help=output_help)
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_PATH), help="Environment config file (YAML)")
    parser.add_argument(
        "--params-file",
        default=str(default_params_path),
        help=f"Run parameter JSON (defaults to {default_params_path})",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser


def load_params(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_single_window(
    *,
    args,
    default_params_path: Path,
    build_config_fn: Callable[..., Any],
    default_window_days: int,
):
    data_dir = Path(args.data_dir).resolve() if getattr(args, "data_dir", None) else None
    output_dir = Path(args.output_dir).resolve() if getattr(args, "output_dir", None) else None
    env_file = Path(args.env_file).resolve() if getattr(args, "env_file", None) else None
    config = build_config_fn(data_dir=data_dir, output_dir=output_dir, environment_path=env_file)

    params_path = Path(getattr(args, "params_file", default_params_path)).resolve()
    params = load_params(params_path)

    args.country = getattr(args, "country", None) or params.get("country")
    args.fasin = getattr(args, "fasin", None) or params.get("fasin")
    if not args.country or not args.fasin:
        raise ValueError("country and fasin must be provided either via CLI arguments or params file")

    resolved_window_days = (
        getattr(args, "window_days", None)
        or coerce_int(params.get("window_days"))
        or default_window_days
    )
    args.window_days = resolved_window_days

    default_biz_date = date.today() - timedelta(days=1)
    biz_date_value = getattr(args, "biz_date", None) or params.get("biz_date") or default_biz_date
    start_override = getattr(args, "start_date", None) or params.get("start_date")
    end_override = getattr(args, "end_date", None) or params.get("end_date")

    start_date, end_date = resolve_window(
        start_date=start_override,
        end_date=end_override,
        biz_date=biz_date_value,
        window_days=resolved_window_days,
    )
    return config, start_date, end_date


def format_window(start_date: date, end_date: date) -> Tuple[str, str]:
    return format_date(start_date), format_date(end_date)


# ---------- IO helpers ----------
def write_table(path: Path, table_name: str, records: Iterable[Dict] | Dict, *, key_override: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(records, dict):
        records = [records]
    payload_key = key_override or table_name
    payload = {payload_key: list(records)}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


# ---------- Date helpers ----------
def ensure_full_day_range(start_date: str, end_date: str) -> Tuple[str, str]:
    start_ts = f"{start_date} 00:00:00" if len(start_date) == 10 else start_date
    end_ts = f"{end_date} 23:59:59" if len(end_date) == 10 else end_date
    return start_ts, end_ts
