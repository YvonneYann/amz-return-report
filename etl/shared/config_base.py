from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = BASE_DIR / "config" / "environment.yaml"


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


def apply_threshold_overrides(thresholds: ThresholdConfig, overrides: Dict[str, Any]) -> ThresholdConfig:
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
