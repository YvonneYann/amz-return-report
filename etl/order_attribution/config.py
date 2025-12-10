from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import DEFAULT_ENV_PATH, DatabaseConfig, ThresholdConfig as BaseThresholdConfig, load_database_config

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = BASE_DIR / "template" / "order_attribution" / "input"
DEFAULT_OUTPUT_DIR = BASE_DIR / "template" / "order_attribution" / "output"

# Reuse the same thresholds and defaults as the return view.
ThresholdConfig = BaseThresholdConfig


def _apply_threshold_overrides(thresholds: ThresholdConfig, overrides: Dict[str, Any]) -> ThresholdConfig:
    """Apply optional overrides to the shared threshold config."""
    for key, value in overrides.items():
        if value is None or not hasattr(thresholds, key):
            continue
        current = getattr(thresholds, key)
        try:
            coerced = type(current)(value)
        except Exception:
            coerced = value
        setattr(thresholds, key, coerced)
    return thresholds


@dataclass
class PathConfig:
    data_dir: Path = DEFAULT_DATA_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR


@dataclass
class PipelineConfig:
    paths: PathConfig = field(default_factory=PathConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    default_window_days: int = 90


def build_config(
    *,
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    window_days: Optional[int] = None,
    environment_path: Optional[Path] = None,
    threshold_overrides: Optional[Dict[str, Any]] = None,
) -> PipelineConfig:
    db_conf = load_database_config(environment_path or DEFAULT_ENV_PATH)
    thresholds = _apply_threshold_overrides(ThresholdConfig(), threshold_overrides or {})
    paths = PathConfig(
        data_dir=data_dir or DEFAULT_DATA_DIR,
        output_dir=output_dir or DEFAULT_OUTPUT_DIR,
    )
    config = PipelineConfig(paths=paths, database=db_conf, thresholds=thresholds)
    if window_days is not None:
        config.default_window_days = int(window_days)
    return config
