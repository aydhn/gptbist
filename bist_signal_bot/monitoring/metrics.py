import math
from datetime import datetime
from typing import Any
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType, MonitoringWindow, MonitoringStatus

class MonitoringMetricCalculator:
    def calculate_metrics(self, object_type: MonitoringObjectType, object_id: str, outcomes: list[Any], as_of: datetime | None = None) -> list[MonitoringMetric]:
        as_of = as_of or datetime.now()
        metrics = []

        # Example implementations; would be tailored to specific outcomes
        wr = self.win_rate(outcomes)
        metrics.append(MonitoringMetric(
            metric_id=f"win_rate_{object_id}",
            object_type=object_type,
            object_id=object_id,
            metric_name="win_rate",
            window=MonitoringWindow.SHORT,
            value=wr,
            sample_count=len(outcomes),
            as_of=as_of,
            status=self.status_from_metric("win_rate", wr, None, len(outcomes))
        ))

        ex = self.expectancy(outcomes)
        metrics.append(MonitoringMetric(
            metric_id=f"expectancy_{object_id}",
            object_type=object_type,
            object_id=object_id,
            metric_name="expectancy",
            window=MonitoringWindow.SHORT,
            value=ex,
            sample_count=len(outcomes),
            as_of=as_of,
            status=self.status_from_metric("expectancy", ex, None, len(outcomes))
        ))

        pf = self.profit_factor(outcomes)
        metrics.append(MonitoringMetric(
            metric_id=f"profit_factor_{object_id}",
            object_type=object_type,
            object_id=object_id,
            metric_name="profit_factor",
            window=MonitoringWindow.SHORT,
            value=pf,
            sample_count=len(outcomes),
            as_of=as_of,
            status=self.status_from_metric("profit_factor", pf, None, len(outcomes))
        ))

        returns = [getattr(o, 'return_pct', 0.0) for o in outcomes if hasattr(o, 'return_pct')]
        if not returns and outcomes and isinstance(outcomes[0], float):
            returns = outcomes

        dd = self.max_drawdown_from_returns(returns)
        metrics.append(MonitoringMetric(
            metric_id=f"max_drawdown_{object_id}",
            object_type=object_type,
            object_id=object_id,
            metric_name="max_drawdown",
            window=MonitoringWindow.SHORT,
            value=dd,
            sample_count=len(returns),
            as_of=as_of,
            status=self.status_from_metric("max_drawdown", dd, None, len(returns))
        ))

        return metrics

    def win_rate(self, outcomes: list[Any]) -> float | None:
        if not outcomes:
            return None

        wins = 0
        total = 0
        for out in outcomes:
            val = getattr(out, 'return_pct', None)
            if val is None and isinstance(out, (float, int)):
                val = float(out)
            if val is not None and not math.isnan(val):
                total += 1
                if val > 0:
                    wins += 1

        if total == 0:
            return None
        return wins / total

    def average_return(self, outcomes: list[Any]) -> float | None:
        if not outcomes:
            return None
        total_ret = 0.0
        count = 0
        for out in outcomes:
            val = getattr(out, 'return_pct', None)
            if val is None and isinstance(out, (float, int)):
                val = float(out)
            if val is not None and not math.isnan(val):
                total_ret += val
                count += 1
        if count == 0:
            return None
        return total_ret / count

    def expectancy(self, outcomes: list[Any]) -> float | None:
        if not outcomes:
            return None

        wins = []
        losses = []

        for out in outcomes:
            val = getattr(out, 'return_pct', None)
            if val is None and isinstance(out, (float, int)):
                val = float(out)
            if val is not None and not math.isnan(val):
                if val > 0:
                    wins.append(val)
                elif val < 0:
                    losses.append(val)

        total = len(wins) + len(losses)
        if total == 0:
            return None

        win_rate = len(wins) / total
        loss_rate = len(losses) / total

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0

        return (win_rate * avg_win) - (loss_rate * avg_loss)

    def profit_factor(self, outcomes: list[Any]) -> float | None:
        if not outcomes:
            return None

        gross_profit = 0.0
        gross_loss = 0.0

        for out in outcomes:
            val = getattr(out, 'return_pct', None)
            if val is None and isinstance(out, (float, int)):
                val = float(out)
            if val is not None and not math.isnan(val):
                if val > 0:
                    gross_profit += val
                elif val < 0:
                    gross_loss += abs(val)

        if gross_loss == 0.0:
            return float('inf') if gross_profit > 0 else None

        return gross_profit / gross_loss

    def max_drawdown_from_returns(self, returns: list[float]) -> float | None:
        if not returns:
            return None

        peak = 1.0
        current_eq = 1.0
        max_dd = 0.0

        for ret in returns:
            if not math.isnan(ret):
                current_eq *= (1 + ret)
                if current_eq > peak:
                    peak = current_eq
                dd = (peak - current_eq) / peak
                if dd > max_dd:
                    max_dd = dd

        return max_dd

    def sharpe_like_score(self, returns: list[float]) -> float | None:
        if not returns:
            return None

        valid_rets = [r for r in returns if not math.isnan(r)]
        if not valid_rets:
            return None

        avg_ret = sum(valid_rets) / len(valid_rets)
        variance = sum((r - avg_ret) ** 2 for r in valid_rets) / len(valid_rets)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return None

        return avg_ret / std_dev

    def calibration_reliability(self, outcomes: list[Any]) -> float | None:
        if not outcomes:
            return None

        # Mock calculation for reliability based on outcomes matching expected values.
        # This requires more complex logic to map expected vs actual.
        # For MVP we will just return a score based on variance.
        valid_rets = []
        for out in outcomes:
            val = getattr(out, 'return_pct', None)
            if val is None and isinstance(out, (float, int)):
                val = float(out)
            if val is not None and not math.isnan(val):
                valid_rets.append(val)

        if len(valid_rets) < 2:
            return None

        avg = sum(valid_rets) / len(valid_rets)
        variance = sum((r - avg) ** 2 for r in valid_rets) / len(valid_rets)
        # Closer to 0 variance is more reliable, let's inverse it 0-1 range.
        rel = 1.0 / (1.0 + variance)
        return rel

    def status_from_metric(self, metric_name: str, value: float | None, baseline: float | None, sample_count: int | None) -> MonitoringStatus:
        if sample_count is None or sample_count < 30:
            return MonitoringStatus.INSUFFICIENT_DATA

        if value is None:
            return MonitoringStatus.UNKNOWN

        if baseline is not None:
            # Check decay
            if value < baseline * 0.8: # 20% drop
                return MonitoringStatus.DEGRADED
            elif value < baseline * 0.9: # 10% drop
                return MonitoringStatus.WATCH

        # Static thresholds
        if metric_name == "win_rate":
            if value < 0.4: return MonitoringStatus.DEGRADED
            if value < 0.5: return MonitoringStatus.WATCH
        elif metric_name == "profit_factor":
            if value < 1.0: return MonitoringStatus.DEGRADED
            if value < 1.2: return MonitoringStatus.WATCH

        return MonitoringStatus.PASS
