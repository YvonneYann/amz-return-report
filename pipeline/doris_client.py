from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .utils import parse_review_date, parse_snapshot_date


def _read_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_snapshot_rows(path: Path) -> List[Dict]:
    payload = _read_json(path)
    rows = payload.get("view_return_snapshot", [])
    parsed = []
    for row in rows:
        parsed.append(
            {
                "country": row["country"],
                "fasin": row["fasin"],
                "asin": row["asin"],
                "snapshot_date": parse_snapshot_date(row["snapshot_date"]),
                "units_sold": int(row["units_sold"]),
                "units_returned": int(row["units_returned"]),
            }
        )
    return parsed


def load_fact_rows(path: Path) -> List[Dict]:
    payload = _read_json(path)
    rows = payload.get("view_return_fact_details", [])
    parsed = []
    for row in rows:
        parsed.append(
            {
                "country": row["country"],
                "fasin": row["fasin"],
                "asin": row["asin"],
                "review_id": row.get("review_id"),
                "review_source": int(row.get("review_source", 0)),
                "review_date": parse_review_date(row["review_date"]),
                "tag_code": row.get("tag_code"),
                "tag_name_cn": row.get("tag_name_cn"),
                "review_en": row.get("review_en"),
                "review_cn": row.get("review_cn"),
            }
        )
    return parsed


def load_tag_dim(path: Optional[Path]) -> Dict[str, str]:
    if path is None or not path.exists():
        return {}
    payload = _read_json(path)
    tags = {}
    for row in payload.get("return_dim_tag", []):
        tags[row["tag_code"]] = row.get("tag_name_cn") or row["tag_code"]
    return tags