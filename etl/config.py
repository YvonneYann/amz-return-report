from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = BASE_DIR / "config" / "environment.yaml"
DEFAULT_DATA_DIR = BASE_DIR / "template" / "input"
DEFAULT_OUTPUT_DIR = BASE_DIR / "template" / "output"


@dataclass
class DatabaseConfig:
    host: str = ""
    port: int = 9030
    database: str = ""
    username: str = ""
    password: str = ""


@dataclass
class ThresholdConfig:
    warn_return_rate: float = 0.10
    high_return_buffer: float = 0.02
    min_sales_share_a: float = 0.10
    min_returns_share_a: float = 0.10
    min_sales_share_b: float = 0.05
    min_returns_share_b: float = 0.05
    min_units_returned_b: int = 10
    watchlist_threshold: float = 0.05
    top_asin_rows: int = 10
    coverage_threshold: float = 0.80
    max_core_reasons: int = 3
    min_core_reasons: int = 1
    text_sample_high: int = 30
    text_sample_medium: int = 15
    text_coverage_high: float = 0.10
    text_coverage_medium: float = 0.05


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


def _convert_value(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    lowered = value.lower()
    if lowered in {"null", "none"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def _parse_simple_yaml(path: Path) -> Dict[str, Dict[str, Any]]:
    """Lightweight YAML parser that is sufficient for our environment file."""
    result: Dict[str, Dict[str, Any]] = {}
    current_key: Optional[str] = None
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if stripped.startswith("\ufeff"):
                stripped = stripped.lstrip("\ufeff")
            if not stripped or stripped.startswith("#"):
                continue
            if not raw_line.startswith(" "):
                if stripped.endswith(":"):
                    current_key = stripped[:-1]
                    result[current_key] = {}
                else:
                    key, _, value = stripped.partition(":")
                    key = key.lstrip("\ufeff")
                    result[key.strip()] = {"value": _convert_value(value)}
                    current_key = None
            else:
                if current_key is None:
                    continue
                key, _, value = stripped.partition(":")
                key = key.lstrip("\ufeff")
                result[current_key][key.strip()] = _convert_value(value)
    return result


def load_database_config(environment_path: Optional[Path] = None) -> DatabaseConfig:
    env_path = environment_path or DEFAULT_ENV_PATH
    parsed = _parse_simple_yaml(env_path)
    doris_block = parsed.get("doris", {})
    return DatabaseConfig(
        host=str(doris_block.get("host", "") or ""),
        port=int(doris_block.get("port", 9030) or 9030),
        database=str(doris_block.get("database", "") or ""),
        username=str(doris_block.get("username", "") or ""),
        password=str(doris_block.get("password", "") or ""),
    )


def build_config(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    environment_path: Optional[Path] = None,
) -> PipelineConfig:
    db_conf = load_database_config(environment_path)
    paths = PathConfig(
        data_dir=data_dir or DEFAULT_DATA_DIR,
        output_dir=output_dir or DEFAULT_OUTPUT_DIR,
    )
    return PipelineConfig(database=db_conf, paths=paths)
