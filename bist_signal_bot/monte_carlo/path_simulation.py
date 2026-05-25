import uuid
from typing import Any

from bist_signal_bot.monte_carlo.models import MonteCarloRequest, MonteCarloPath

class PathSimulator:
    def equity_curve_from_returns(self, returns: list[float], initial_equity: float) -> list[float]:
        curve = [initial_equity]
        current = initial_equity
        for r in returns:
            current *= (1 + r / 100.0)
            curve.append(current)
        return curve

    def equity_curve_from_trades(self, trades: list[dict[str, Any]], initial_equity: float, use_net: bool = True) -> list[float]:
        curve = [initial_equity]
        current = initial_equity
        key = "net_return_pct" if use_net else "gross_return_pct"
        for t in trades:
            ret = t.get(key, 0.0)
            current *= (1 + ret / 100.0)
            curve.append(current)
        return curve

    def max_drawdown_pct(self, equity_curve: list[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        for val in equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def ruin_hit(self, equity_curve: list[float], initial_equity: float, ruin_threshold_pct: float) -> bool:
        if not equity_curve:
            return False
        ruin_level = initial_equity * (1 - ruin_threshold_pct / 100.0)
        return any(val <= ruin_level for val in equity_curve)

    def simulate_paths_from_returns(self, simulated_returns: list[list[float]], request: MonteCarloRequest) -> list[MonteCarloPath]:
        paths = []
        for i, returns in enumerate(simulated_returns):
            curve = self.equity_curve_from_returns(returns, request.initial_equity)
            final_equity = curve[-1] if curve else request.initial_equity
            tr = (final_equity - request.initial_equity) / request.initial_equity * 100.0
            mdd = self.max_drawdown_pct(curve)
            ruin = self.ruin_hit(curve, request.initial_equity, request.ruin_threshold_pct)

            paths.append(MonteCarloPath(
                path_id=str(uuid.uuid4()),
                simulation_index=i,
                equity_curve=curve,
                returns=returns,
                trades_count=len(returns),
                final_equity=final_equity,
                total_return_pct=tr,
                max_drawdown_pct=mdd,
                ruin_hit=ruin,
                metadata={"use_net": True}
            ))
        return paths

    def simulate_paths_from_trades(self, simulated_trades: list[list[dict[str, Any]]], request: MonteCarloRequest) -> list[MonteCarloPath]:
        paths = []
        for i, trades in enumerate(simulated_trades):
            curve = self.equity_curve_from_trades(trades, request.initial_equity, use_net=True)
            final_equity = curve[-1] if curve else request.initial_equity
            tr = (final_equity - request.initial_equity) / request.initial_equity * 100.0
            mdd = self.max_drawdown_pct(curve)
            ruin = self.ruin_hit(curve, request.initial_equity, request.ruin_threshold_pct)
            returns = [t.get("net_return_pct", 0.0) for t in trades]

            paths.append(MonteCarloPath(
                path_id=str(uuid.uuid4()),
                simulation_index=i,
                equity_curve=curve,
                returns=returns,
                trades_count=len(trades),
                final_equity=final_equity,
                total_return_pct=tr,
                max_drawdown_pct=mdd,
                ruin_hit=ruin,
                metadata={"use_net": True}
            ))
        return paths
