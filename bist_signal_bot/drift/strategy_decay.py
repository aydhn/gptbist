import uuid
import logging
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    StrategyDecayReport, DriftStatus, DriftSeverity, DriftAction
)
from bist_signal_bot.drift.statistics import DriftStatistics

logger = logging.getLogger(__name__)

class StrategyDecayAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def analyze(self, strategy_name: str, reference_runs: list[Any], current_runs: list[Any]) -> StrategyDecayReport:
        report = StrategyDecayReport(
            report_id=str(uuid.uuid4()),
            strategy_name=strategy_name
        )

        if len(reference_runs) == 0 or len(current_runs) == 0:
             report.status = DriftStatus.INSUFFICIENT_DATA
             report.warnings.append("Insufficient strategy runs for decay analysis.")
             return report

        ref_metrics = self.extract_strategy_metrics(reference_runs)
        cur_metrics = self.extract_strategy_metrics(current_runs)

        report.reference_metrics = ref_metrics
        report.current_metrics = cur_metrics

        changes = self.metric_changes(ref_metrics, cur_metrics)
        report.metric_changes = changes

        decay_score = self.calculate_decay_score(changes)
        report.decay_score = decay_score

        if self.settings.DRIFT_STRATEGY_DECAY_SCORE_FAIL is not None and decay_score >= self.settings.DRIFT_STRATEGY_DECAY_SCORE_FAIL:
             report.status = DriftStatus.DRIFTING
             report.severity = DriftSeverity.HIGH
        elif self.settings.DRIFT_STRATEGY_DECAY_SCORE_WARN is not None and decay_score >= self.settings.DRIFT_STRATEGY_DECAY_SCORE_WARN:
             report.status = DriftStatus.WATCH
             report.severity = DriftSeverity.MEDIUM
        else:
             report.status = DriftStatus.STABLE
             report.severity = DriftSeverity.LOW

        report.recommended_actions = self.build_actions(report)
        return report

    def extract_strategy_metrics(self, runs: list[Any]) -> dict[str, Any]:
        avg_return_raw = []
        win_rate_raw = []
        profit_factor_raw = []
        sharpe_raw = []
        drawdown_raw = []

        # Localize keys for faster access
        keys_return = ('return_pct', 'total_return', 'avg_return')
        keys_win = ('win_rate', 'win_pct')
        keys_profit = ('profit_factor',)
        keys_sharpe = ('sharpe', 'sharpe_ratio')
        keys_drawdown = ('max_drawdown', 'drawdown')

        for r in runs:
            if isinstance(r, dict):
                # return
                v = None
                for k in keys_return:
                    if k in r: v = r[k]; break
                avg_return_raw.append(v)

                # win
                v = None
                for k in keys_win:
                    if k in r: v = r[k]; break
                win_rate_raw.append(v)

                # profit
                v = None
                for k in keys_profit:
                    if k in r: v = r[k]; break
                profit_factor_raw.append(v)

                # sharpe
                v = None
                for k in keys_sharpe:
                    if k in r: v = r[k]; break
                sharpe_raw.append(v)

                # drawdown
                v = None
                for k in keys_drawdown:
                    if k in r: v = r[k]; break
                drawdown_raw.append(v)
            else:
                # return
                v = None
                for k in keys_return:
                    if hasattr(r, k): v = getattr(r, k); break
                avg_return_raw.append(v)

                # win
                v = None
                for k in keys_win:
                    if hasattr(r, k): v = getattr(r, k); break
                win_rate_raw.append(v)

                # profit
                v = None
                for k in keys_profit:
                    if hasattr(r, k): v = getattr(r, k); break
                profit_factor_raw.append(v)

                # sharpe
                v = None
                for k in keys_sharpe:
                    if hasattr(r, k): v = getattr(r, k); break
                sharpe_raw.append(v)

                # drawdown
                v = None
                for k in keys_drawdown:
                    if hasattr(r, k): v = getattr(r, k); break
                drawdown_raw.append(v)

        avg_return = DriftStatistics.safe_numeric_series(avg_return_raw)
        win_rate = DriftStatistics.safe_numeric_series(win_rate_raw)
        profit_factor = DriftStatistics.safe_numeric_series(profit_factor_raw)
        sharpe = DriftStatistics.safe_numeric_series(sharpe_raw)
        drawdown = DriftStatistics.safe_numeric_series(drawdown_raw)

        return {
             "average_return": sum(avg_return)/len(avg_return) if avg_return else None,
             "win_rate": sum(win_rate)/len(win_rate) if win_rate else None,
             "profit_factor": sum(profit_factor)/len(profit_factor) if profit_factor else None,
             "sharpe": sum(sharpe)/len(sharpe) if sharpe else None,
             "max_drawdown": sum(drawdown)/len(drawdown) if drawdown else None,
             "run_count": len(runs)
        }

    def metric_changes(self, reference: dict[str, Any], current: dict[str, Any]) -> dict[str, float | None]:
        changes = {}
        for k in ["average_return", "win_rate", "profit_factor", "sharpe", "max_drawdown"]:
             ref_v = reference.get(k)
             cur_v = current.get(k)

             if ref_v is not None and cur_v is not None:
                  if k == "max_drawdown":
                       changes[k] = float(cur_v - ref_v)
                  else:
                       changes[k] = DriftStatistics.rate_change(ref_v, cur_v)
             else:
                  changes[k] = None
        return changes

    def calculate_decay_score(self, changes: dict[str, float | None]) -> float:
        score = 0.0

        pf_change = changes.get("profit_factor")
        if pf_change is not None and pf_change < 0:
             score += min(abs(pf_change) * 0.5, 30.0)

        sharpe_change = changes.get("sharpe")
        if sharpe_change is not None and sharpe_change < 0:
             score += min(abs(sharpe_change) * 0.5, 30.0)

        dd_change = changes.get("max_drawdown")
        if dd_change is not None and dd_change > 0:
             score += min(dd_change * 2.0, 40.0)

        return float(min(score, 100.0))

    def build_actions(self, report: StrategyDecayReport) -> list[DriftAction]:
        actions = set()

        if report.status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT]:
             actions.add(DriftAction.WATCH)
             actions.add(DriftAction.RUN_BACKTEST)
             actions.add(DriftAction.RUN_OPTIMIZATION)
             if report.decay_score >= 80.0:
                 actions.add(DriftAction.MARK_WATCH_ONLY)
        elif report.status == DriftStatus.WATCH:
             actions.add(DriftAction.WATCH)
             actions.add(DriftAction.REVIEW_MANUALLY)

        if not actions:
             actions.add(DriftAction.NO_ACTION)

        return list(actions)
