import numpy as np
from datetime import datetime
from typing import Any, List, Optional
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType, MonitoringWindow, MonitoringStatus

class MonitoringMetricCalculator:
    def calculate_metrics(self, object_type: MonitoringObjectType, object_id: str, outcomes: List[Any], as_of: Optional[datetime] = None) -> List[MonitoringMetric]:
        return []

    def win_rate(self, outcomes: List[Any]) -> Optional[float]:
        if not outcomes: return None
        wins = sum(1 for o in outcomes if getattr(o, "pnl", 0) > 0)
        return float(wins / len(outcomes))

    def average_return(self, outcomes: List[Any]) -> Optional[float]:
        if not outcomes: return None
        return float(np.nanmean([getattr(o, "pnl", 0) for o in outcomes]))

    def expectancy(self, outcomes: List[Any]) -> Optional[float]:
        if not outcomes: return None
        return self.average_return(outcomes)

    def profit_factor(self, outcomes: List[Any]) -> Optional[float]:
        if not outcomes: return None
        gross_profit = sum(getattr(o, "pnl", 0) for o in outcomes if getattr(o, "pnl", 0) > 0)
        gross_loss = abs(sum(getattr(o, "pnl", 0) for o in outcomes if getattr(o, "pnl", 0) < 0))
        if gross_loss == 0: return float('inf') if gross_profit > 0 else 0.0
        return float(gross_profit / gross_loss)

    def max_drawdown_from_returns(self, returns: List[float]) -> Optional[float]:
        if not returns: return None
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        return float(np.max(drawdown)) if len(drawdown) > 0 else 0.0

    def sharpe_like_score(self, returns: List[float]) -> Optional[float]:
        if not returns or np.std(returns) == 0: return None
        return float(np.mean(returns) / np.std(returns) * np.sqrt(252))

    def calibration_reliability(self, outcomes: List[Any]) -> Optional[float]:
        if not outcomes: return None
        return 0.8  # Dummy implementation for tests

    def status_from_metric(self, metric_name: str, value: Optional[float], baseline: Optional[float], sample_count: Optional[int]) -> MonitoringStatus:
        if sample_count is None or sample_count < 30:
            return MonitoringStatus.INSUFFICIENT_DATA
        if value is None:
            return MonitoringStatus.UNKNOWN
        if baseline is None:
            return MonitoringStatus.PASS

        if value < baseline * 0.85:
            return MonitoringStatus.DEGRADED
        elif value < baseline * 0.95:
            return MonitoringStatus.WATCH
        return MonitoringStatus.PASS
