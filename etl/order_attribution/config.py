from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import ThresholdConfig

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = BASE_DIR / "template" / "order_attribution" / "input"
DEFAULT_OUTPUT_DIR = BASE_DIR / "template" / "order_attribution" / "output"


@dataclass
class PathConfig:
    data_dir: Path = DEFAULT_DATA_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR


@dataclass
class PipelineConfig:
    paths: PathConfig = field(default_factory=PathConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    default_window_days: int = 90
    default_return_lag_days: int = 35


def build_config(
    *,
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    return_lag_days: Optional[int] = None,
    window_days: Optional[int] = None,
) -> PipelineConfig:
    paths = PathConfig(
        data_dir=data_dir or DEFAULT_DATA_DIR,
        output_dir=output_dir or DEFAULT_OUTPUT_DIR,
    )
    config = PipelineConfig(paths=paths)
    if return_lag_days is not None:
        config.default_return_lag_days = int(return_lag_days)
    if window_days is not None:
        config.default_window_days = int(window_days)
    return config
