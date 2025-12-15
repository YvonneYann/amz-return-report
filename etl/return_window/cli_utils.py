from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Tuple

from ..shared.calculator import format_date
from ..shared.utils import build_single_window_parser, resolve_single_window
from .config import PipelineConfig, build_config
from ..shared.config_base import BASE_DIR

DEFAULT_PARAMS_PATH = BASE_DIR / "config" / "return_window_run_params.json"
DEFAULT_WINDOW_DAYS = PipelineConfig().default_window_days


def build_stage_parser(description: str) -> argparse.ArgumentParser:
    return build_single_window_parser(
        description=description,
        default_params_path=DEFAULT_PARAMS_PATH,
        data_help="Optional override for template/return_window/input directory",
        output_help="Optional override for template/return_window/output directory",
    )


def resolve_runtime(args: argparse.Namespace) -> Tuple[PipelineConfig, date, date]:
    config, start_date, end_date = resolve_single_window(
        args=args,
        default_params_path=DEFAULT_PARAMS_PATH,
        build_config_fn=build_config,
        default_window_days=DEFAULT_WINDOW_DAYS,
    )
    return config, start_date, end_date


def format_window(start_date: date, end_date: date) -> Tuple[str, str]:
    return format_date(start_date), format_date(end_date)
