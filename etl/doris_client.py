from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pymysql
from pymysql.cursors import DictCursor

from .config import DatabaseConfig, PathConfig


class DorisClient:
    """Client that pulls fresh data from Doris and caches it locally."""

    SNAPSHOT_SQL = (
        "SELECT country, fasin, asin, snapshot_date, units_sold, units_returned "
        "FROM view_return_snapshot "
        "WHERE country = %s AND fasin = %s AND snapshot_date BETWEEN %s AND %s"
    )
    FACT_SQL = (
        "SELECT country, fasin, asin, review_id, review_source, review_date, tag_code, "
        "review_en, review_cn, sentiment, tag_name_cn, evidence, created_at, updated_at "
        "FROM view_return_fact_details "
        "WHERE country = %s AND fasin = %s AND review_source IN (0, 1) "
        "AND review_date BETWEEN %s AND %s"
    )
    TAG_SQL = (
        "SELECT tag_code, tag_name_cn, category_code, category_name_cn, level, "
        "definition, boundary_note, is_active, version, effective_from, effective_to, "
        "created_at, updated_at "
        "FROM return_dim_tag"
    )

    def __init__(self, database: DatabaseConfig, paths: PathConfig) -> None:
        self.database = database
        self.data_dir = Path(paths.data_dir)
        self.output_dir = Path(paths.output_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[pymysql.connections.Connection] = None

    def __enter__(self) -> "DorisClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _connect(self) -> pymysql.connections.Connection:
        if self._connection is None:
            self._connection = pymysql.connect(
                host=self.database.host,
                port=self.database.port,
                user=self.database.username,
                password=self.database.password,
                database=self.database.database,
                cursorclass=DictCursor,
                charset="utf8mb4",
            )
        return self._connection

    def _execute_query(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        connection = self._connect()
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [self._normalize_row(row) for row in rows]

    @staticmethod
    def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                normalized[key] = value.isoformat()
            elif isinstance(value, Decimal):
                normalized[key] = float(value)
            else:
                normalized[key] = value
        return normalized

    def _write_dataset(self, table_name: str, records: Any, directory: Optional[Path] = None) -> Path:
        directory = directory or self.data_dir
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{table_name}.json"
        payload = {table_name: records}
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return file_path

    def fetch_view_return_snapshot(
        self,
        *,
        country: str,
        fasin: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        rows = self._execute_query(self.SNAPSHOT_SQL, (country, fasin, start_date, end_date))
        self._write_dataset("view_return_snapshot", rows)
        return rows

    def fetch_view_return_fact_details(
        self,
        *,
        country: str,
        fasin: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        rows = self._execute_query(self.FACT_SQL, (country, fasin, start_date, end_date))
        self._write_dataset("view_return_fact_details", rows)
        return rows

    def fetch_return_dim_tag(self) -> List[Dict[str, Any]]:
        rows = self._execute_query(self.TAG_SQL, tuple())
        self._write_dataset("return_dim_tag", rows)
        return rows

    def write_json(self, table_name: str, records: Any) -> Path:
        return self._write_dataset(table_name, records, self.output_dir)

