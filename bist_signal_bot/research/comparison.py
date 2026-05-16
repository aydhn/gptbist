import uuid
import logging
from typing import Any
from datetime import datetime

from ..config.settings import Settings, get_settings
from .models import ResearchComparisonReport, ResearchComparisonItem, ResearchRunType, ResearchRun
from .ledger import ResearchLedger
from ..core.exceptions import ResearchComparisonError

class ResearchComparator:
    def __init__(self, ledger: ResearchLedger, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.ledger = ledger
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def _get_metric_value(self, item: ResearchComparisonItem, metric: str) -> float | None:
        return item.metrics.get(metric)

    def rank_items(self, items: list[ResearchComparisonItem], metric: str | None = None) -> list[ResearchComparisonItem]:
        metric = metric or self.settings.RESEARCH_DEFAULT_COMPARE_METRIC
        # Determine sort direction. Usually higher is better, except for max_drawdown_pct
        reverse = True
        if "drawdown" in metric.lower() or "elapsed" in metric.lower() or "error" in metric.lower():
            reverse = False

        def sort_key(item: ResearchComparisonItem):
            val = self._get_metric_value(item, metric)
            if val is None:
                return (float('-inf') if reverse else float('inf'), item.run_id)
            return (val, item.run_id)

        items.sort(key=sort_key, reverse=reverse)
        for i, item in enumerate(items):
            item.rank = i + 1
            item.score = self._get_metric_value(item, metric)
        return items

    def _build_report(self, title: str, runs: list[ResearchRun], sort_metric: str) -> ResearchComparisonReport:
        items = []
        for run in runs:
            items.append(ResearchComparisonItem(
                run_id=run.run_id,
                run_type=run.run_type,
                label=f"{run.strategy_name} on {','.join(run.symbols)}",
                metrics=run.metrics
            ))

        ranked = self.rank_items(items, sort_metric)

        best = ranked[0].run_id if ranked else None
        worst = ranked[-1].run_id if ranked else None

        return ResearchComparisonReport(
            comparison_id=f"cmp_{uuid.uuid4().hex[:8]}",
            title=title,
            items=ranked,
            sort_metric=sort_metric,
            best_run_id=best,
            worst_run_id=worst
        )

    def compare_runs(self, run_ids: list[str], sort_metric: str | None = None) -> ResearchComparisonReport:
        runs = []
        for rid in run_ids:
            run = self.ledger.get_run(rid)
            if run:
                runs.append(run)
            else:
                self.logger.warning(f"Run {rid} not found for comparison.")

        if not runs:
            raise ResearchComparisonError("No valid runs found to compare.")

        metric = sort_metric or self.settings.RESEARCH_DEFAULT_COMPARE_METRIC
        return self._build_report(f"Compare Runs by {metric}", runs, metric)

    def compare_strategy(self, symbol: str, strategies: list[str], metric: str = "sharpe") -> ResearchComparisonReport:
        from .models import ResearchQuery
        query = ResearchQuery(symbols=[symbol], strategies=strategies)
        runs = [e.run for e in self.ledger.load_entries(limit=50, query=query)]
        if not runs:
             raise ResearchComparisonError(f"No runs found for symbol {symbol} and given strategies.")
        return self._build_report(f"Strategy comparison for {symbol}", runs, metric)

    def compare_params(self, strategy_name: str, symbol: str, metric: str = "composite_score") -> ResearchComparisonReport:
        from .models import ResearchQuery
        query = ResearchQuery(symbols=[symbol], strategies=[strategy_name], run_types=[ResearchRunType.OPTIMIZATION])
        runs = [e.run for e in self.ledger.load_entries(limit=50, query=query)]
        if not runs:
            raise ResearchComparisonError(f"No optimization runs found for {strategy_name} on {symbol}")
        return self._build_report(f"Parameter comparison for {strategy_name} on {symbol}", runs, metric)

    def compare_recent(self, run_type: ResearchRunType, limit: int = 20, metric: str | None = None) -> ResearchComparisonReport:
        from .models import ResearchQuery
        query = ResearchQuery(run_types=[run_type], limit=limit)
        runs = [e.run for e in self.ledger.load_entries(limit=limit, query=query)]
        if not runs:
             raise ResearchComparisonError(f"No recent runs of type {run_type.value}")
        m = metric or self.settings.RESEARCH_DEFAULT_COMPARE_METRIC
        return self._build_report(f"Recent {run_type.value} Comparison", runs, m)
