from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class ReasonConfidenceThresholds:
    high_min_samples: int = 30
    high_min_coverage: float = 0.10
    medium_min_samples: int = 15
    medium_min_coverage: float = 0.05


@dataclass
class ReasonSelectionRules:
    coverage_threshold: float = 0.80
    max_reasons_when_confident: int = 3
    max_reasons_when_low_confidence: int = 1


@dataclass
class ComputationParams:
    country: str
    parent_asin: str
    start_date: date
    end_date: date
    min_main_sales_share: float = 0.10
    min_main_returns_share: float = 0.10
    warn_return_rate_threshold: float = 0.10
    problem_rate_margin: float = 0.02
    min_problem_units_returned: int = 10
    min_problem_share: float = 0.05
    problem_watchlist_share_max: float = 0.05
    top_asin_limit: Optional[int] = 10
    reason_thresholds: ReasonConfidenceThresholds = field(default_factory=ReasonConfidenceThresholds)
    reason_selection: ReasonSelectionRules = field(default_factory=ReasonSelectionRules)

    def high_return_rate_threshold(self, parent_return_rate: float) -> float:
        base = max(parent_return_rate, self.warn_return_rate_threshold)
        return base + self.problem_rate_margin