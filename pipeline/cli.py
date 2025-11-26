from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asin_structure import build_asin_structure
from .config import (
    ComputationParams,
    ReasonConfidenceThresholds,
    ReasonSelectionRules,
)
from .doris_client import load_fact_rows, load_snapshot_rows, load_tag_dim
from .parent_summary import build_parent_summary, filter_snapshot_rows
from .problem_reasons import build_problem_reasons, filter_fact_rows
from .utils import parse_snapshot_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Amazon parent ASIN return analysis calculator",
    )
    parser.add_argument("--country", required=True, help="վ��/���ң��� US")
    parser.add_argument("--parent-asin", required=True, help="�� ASIN ���")
    parser.add_argument("--start-date", required=True, help="��ʼ���ڣ�YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="�������ڣ�YYYY-MM-DD")
    parser.add_argument(
        "--snapshot-path",
        default="data/view_return_snapshot.json",
        help="view_return_snapshot JSON ·��",
    )
    parser.add_argument(
        "--fact-path",
        default="data/view_return_fact_details.json",
        help="view_return_fact_details JSON ·��",
    )
    parser.add_argument(
        "--tag-dim-path",
        default="data/return_dim_tag.json",
        help="�˻���ǩά�� JSON ·������ѡ��",
    )
    parser.add_argument(
        "--output",
        help="��� JSON �ļ�·������ָ�����ӡ�� stdout",
    )
    parser.add_argument("--top-asin-limit", type=int, default=10, help="ASIN �ṹ��Ĭ�� Top N��Ĭ�� 10")
    parser.add_argument("--min-main-sales-share", type=float, default=0.10)
    parser.add_argument("--min-main-returns-share", type=float, default=0.10)
    parser.add_argument("--warn-return-rate", type=float, default=0.10)
    parser.add_argument("--problem-rate-margin", type=float, default=0.02)
    parser.add_argument("--min-problem-units-returned", type=int, default=10)
    parser.add_argument("--min-problem-share", type=float, default=0.05)
    parser.add_argument("--problem-watchlist-share-max", type=float, default=0.05)
    parser.add_argument("--coverage-threshold", type=float, default=0.80)
    parser.add_argument("--max-reasons", type=int, default=3)
    parser.add_argument("--max-reasons-low-confidence", type=int, default=1)
    parser.add_argument("--high-sample-threshold", type=int, default=30)
    parser.add_argument("--high-coverage-threshold", type=float, default=0.10)
    parser.add_argument("--medium-sample-threshold", type=int, default=15)
    parser.add_argument("--medium-coverage-threshold", type=float, default=0.05)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    start_date = parse_snapshot_date(args.start_date)
    end_date = parse_snapshot_date(args.end_date)
    if end_date < start_date:
        parser.error("end-date �������� start-date")

    snapshot_rows = load_snapshot_rows(Path(args.snapshot_path))
    fact_rows = load_fact_rows(Path(args.fact_path))
    tag_lookup = load_tag_dim(Path(args.tag_dim_path)) if args.tag_dim_path else {}

    reason_thresholds = ReasonConfidenceThresholds(
        high_min_samples=args.high_sample_threshold,
        high_min_coverage=args.high_coverage_threshold,
        medium_min_samples=args.medium_sample_threshold,
        medium_min_coverage=args.medium_coverage_threshold,
    )
    reason_selection = ReasonSelectionRules(
        coverage_threshold=args.coverage_threshold,
        max_reasons_when_confident=args.max_reasons,
        max_reasons_when_low_confidence=args.max_reasons_low_confidence,
    )

    params = ComputationParams(
        country=args.country,
        parent_asin=args.parent_asin,
        start_date=start_date,
        end_date=end_date,
        min_main_sales_share=args.min_main_sales_share,
        min_main_returns_share=args.min_main_returns_share,
        warn_return_rate_threshold=args.warn_return_rate,
        problem_rate_margin=args.problem_rate_margin,
        min_problem_units_returned=args.min_problem_units_returned,
        min_problem_share=args.min_problem_share,
        problem_watchlist_share_max=args.problem_watchlist_share_max,
        top_asin_limit=args.top_asin_limit,
        reason_thresholds=reason_thresholds,
        reason_selection=reason_selection,
    )

    filtered_snapshots = filter_snapshot_rows(snapshot_rows, params)
    parent_summary = build_parent_summary(filtered_snapshots, params)
    asin_structure = build_asin_structure(filtered_snapshots, parent_summary, params)
    filtered_facts = filter_fact_rows(fact_rows, params)
    problem_reasons = build_problem_reasons(asin_structure, filtered_facts, params, tag_lookup)

    result = {
        "parent_summary": parent_summary,
        "asin_structure": asin_structure,
        "problem_asin_reasons": problem_reasons,
    }
    json_text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(json_text, encoding="utf-8")
    else:
        print(json_text)

if __name__ == "__main__":
    main()
