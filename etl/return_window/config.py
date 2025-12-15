from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..shared.config_base import (
    BASE_DIR,
    DEFAULT_ENV_PATH,
    DatabaseConfig,
    ThresholdConfig,
    apply_threshold_overrides,
    load_database_config,
)

DEFAULT_DATA_DIR = BASE_DIR / "template" / "return_window" / "input"
DEFAULT_OUTPUT_DIR = BASE_DIR / "template" / "return_window" / "output"


@dataclass
class PathConfig:
    data_dir: Path = DEFAULT_DATA_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR


@dataclass
class PipelineConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    default_window_days: int = 30


def build_config(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    environment_path: Optional[Path] = None,
) -> PipelineConfig:
    db_conf = load_database_config(environment_path or DEFAULT_ENV_PATH)
    paths = PathConfig(
        data_dir=data_dir or DEFAULT_DATA_DIR,
        output_dir=output_dir or DEFAULT_OUTPUT_DIR,
    )
    return PipelineConfig(database=db_conf, paths=paths)
