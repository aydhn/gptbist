import uuid
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioSnapshot,
    BasketSimulationResult
)

class BasketSimulator:

    def simulate(self, snapshot: ResearchPortfolioSnapshot, data_by_symbol: dict[str, pd.DataFrame], start_date: datetime, end_date: datetime, initial_value: float = 100000.0) -> BasketSimulationResult:
        warnings = []
        equity_curve = self.build_equity_curve(snapshot, data_by_symbol, start_date, end_date, initial_value)

        if not equity_curve:
            warnings.append("No equity curve generated. Possibly missing data in date range.")
            return BasketSimulationResult(
                simulation_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                snapshot_id=snapshot.snapshot_id,
                start_date=start_date,
                end_date=end_date,
                initial_value=initial_value,
                final_value=initial_value,
                simulated_return_pct=0.0,
                warnings=warnings
            )

        final_val = equity_curve[-1]["portfolio_value"]
        ret_pct = ((final_val / initial_value) - 1.0) * 100.0

        max_dd = self.calculate_max_drawdown(equity_curve)
        vol = self.calculate_volatility(equity_curve)

        item_returns = self.calculate_item_returns(snapshot, data_by_symbol, start_date, end_date)

        # Missing data check
        for sym in [i.symbol for i in snapshot.items if i.final_weight > 0]:
            if sym not in data_by_symbol or data_by_symbol[sym].empty:
                warnings.append(f"Missing data for {sym} in simulation")

        return BasketSimulationResult(
            simulation_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            snapshot_id=snapshot.snapshot_id,
            start_date=start_date,
            end_date=end_date,
            initial_value=initial_value,
            final_value=final_val,
            simulated_return_pct=ret_pct,
            max_drawdown_pct=max_dd,
            volatility_pct=vol,
            item_returns=item_returns,
            equity_curve=equity_curve,
            warnings=warnings
        )

    def build_equity_curve(self, snapshot: ResearchPortfolioSnapshot, data_by_symbol: dict[str, pd.DataFrame], start_date: datetime, end_date: datetime, initial_value: float) -> list[dict[str, Any]]:
        weights = {i.symbol: i.final_weight for i in snapshot.items if i.final_weight > 0}
        if not weights:
            return []

        # Very simple daily rebalanced or buy-and-hold logic. We will do a simple daily return aggregation.
        # Align dates
        all_dates = set()
        for df in data_by_symbol.values():
            if not df.empty:
                # filter by dates
                mask = (df.index >= start_date) & (df.index <= end_date)
                all_dates.update(df[mask].index)

        sorted_dates = sorted(list(all_dates))
        if not sorted_dates:
            return []

        curve = []
        current_val = initial_value

        for i, d in enumerate(sorted_dates):
            if i == 0:
                curve.append({"date": d.isoformat(), "portfolio_value": current_val, "daily_return": 0.0})
                continue

            prev_d = sorted_dates[i-1]
            daily_ret = 0.0
            total_weight_present = 0.0

            for sym, w in weights.items():
                df = data_by_symbol.get(sym)
                if df is not None and not df.empty and d in df.index and prev_d in df.index:
                    p1 = df.loc[prev_d, 'close']
                    p2 = df.loc[d, 'close']
                    if p1 > 0:
                        ret = (p2 - p1) / p1
                        daily_ret += ret * w
                        total_weight_present += w

            # normalize return if some data is missing
            if total_weight_present > 0:
                daily_ret = daily_ret / total_weight_present

            current_val *= (1 + daily_ret)
            curve.append({"date": d.isoformat(), "portfolio_value": current_val, "daily_return": daily_ret})

        return curve

    def calculate_item_returns(self, snapshot: ResearchPortfolioSnapshot, data_by_symbol: dict[str, pd.DataFrame], start_date: datetime, end_date: datetime) -> dict[str, float]:
        returns = {}
        weights = {i.symbol: i.final_weight for i in snapshot.items if i.final_weight > 0}
        for sym in weights.keys():
            df = data_by_symbol.get(sym)
            if df is not None and not df.empty:
                mask = (df.index >= start_date) & (df.index <= end_date)
                sub = df[mask]
                if not sub.empty:
                    p1 = sub.iloc[0]['close']
                    p2 = sub.iloc[-1]['close']
                    if p1 > 0:
                        returns[sym] = ((p2 / p1) - 1.0) * 100.0
        return returns

    def calculate_max_drawdown(self, equity_curve: list[dict[str, Any]]) -> float | None:
        if not equity_curve:
            return None
        vals = [c["portfolio_value"] for c in equity_curve]
        if not vals:
            return 0.0

        peak = vals[0]
        max_dd = 0.0
        for v in vals:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd * 100.0

    def calculate_volatility(self, equity_curve: list[dict[str, Any]]) -> float | None:
        if len(equity_curve) < 2:
            return None
        rets = [c["daily_return"] for c in equity_curve]
        std = np.std(rets)
        return float(std * np.sqrt(252) * 100.0) # Annualized
