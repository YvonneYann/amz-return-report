from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..config import DatabaseConfig, PathConfig, load_database_config
from ..doris_client import DorisClient as _BaseDorisClient
from .config import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


class DorisClient(_BaseDorisClient):
    """
    Order-attribution Doris client that pulls data into the order_attribution template paths,
    using purchase_date windows and return lag-aware sources per order attribution PRD.
    """

    SNAPSHOT_SQL = (
        "SELECT country, fasin, asin, snapshot_date, units_sold, units_returned "
        "FROM view_return_snapshot "
        "WHERE country = %s AND fasin = %s AND snapshot_date BETWEEN %s AND %s"
    )

    ORDERS_SQL = (
        "SELECT country, fasin, asin, review_date, purchase_date, return_deadline, review_id, quantity "
        "FROM view_return_orders_snapshot "
        "WHERE country = %s AND fasin = %s AND purchase_date BETWEEN %s AND %s"
    )

    FACT_SQL = (
        "SELECT country, fasin, asin, review_id, review_source, review_date, purchase_date, return_deadline, "
        "tag_code, review_en, review_cn, sentiment, tag_name_cn, evidence, created_at, updated_at "
        "FROM view_return_fact_details "
        "WHERE country = %s AND fasin = %s AND purchase_date BETWEEN %s AND %s"
    )

    TAG_SQL = (
        "SELECT tag_code, tag_name_cn, category_code, category_name_cn, level, "
        "definition, boundary_note, is_active, version, effective_from, effective_to, "
        "created_at, updated_at "
        "FROM return_dim_tag"
    )

    BI_SNAPSHOT_SQL = (
        "SELECT country, fasin, asin, snapshot_date, payload "
        "FROM view_bi_amz_asin_product_snapshot "
        "WHERE country = %s AND fasin = %s AND snapshot_date BETWEEN %s AND %s"
    )

    def __init__(
        self,
        database: Optional[DatabaseConfig] = None,
        data_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        db_conf = database or load_database_config()
        paths = PathConfig(
            data_dir=data_dir or DEFAULT_DATA_DIR,
            output_dir=output_dir or DEFAULT_OUTPUT_DIR,
        )
        super().__init__(db_conf, paths)

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

    def _execute_query(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        connection = self._connect()
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [self._normalize_row(row) for row in rows]

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

    def fetch_view_return_orders_snapshot(
        self,
        *,
        country: str,
        fasin: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        rows = self._execute_query(self.ORDERS_SQL, (country, fasin, start_date, end_date))
        self._write_dataset("view_return_orders_snapshot", rows)
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

    def fetch_view_bi_amz_asin_product_snapshot(
        self,
        *,
        country: str,
        fasin: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        rows = self._execute_query(self.BI_SNAPSHOT_SQL, (country, fasin, start_date, end_date))
        self._write_dataset("view_bi_amz_asin_product_snapshot", rows)
        return rows
