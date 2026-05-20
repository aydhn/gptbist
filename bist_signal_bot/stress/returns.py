import uuid
import math
import numpy as np
import pandas as pd
from typing import Any
from datetime import datetime

from bist_signal_bot.stress.models import ReturnSeries, StressInputType

class ReturnSeriesBuilder:
    @staticmethod
    def from_price_data(symbol: str, df: pd.DataFrame, source_type: StressInputType = StressInputType.CUSTOM_RETURNS) -> ReturnSeries:
        warnings = []
        if df.empty:
            warnings.append("DataFrame is empty.")
            return ReturnSeries(
                series_id=str(uuid.uuid4()),
                symbol=symbol,
                source_type=source_type,
                returns=[],
                frequency="1D",
                warnings=warnings
            )

        if "Close" not in df.columns:
            warnings.append("Close column not found in DataFrame.")
            return ReturnSeries(
                series_id=str(uuid.uuid4()),
                symbol=symbol,
                source_type=source_type,
                returns=[],
                frequency="1D",
                warnings=warnings
            )

        close_series = df["Close"].dropna()
        if len(close_series) < 2:
            warnings.append("Not enough data to calculate returns.")
            returns = []
        else:
            returns = close_series.pct_change().dropna().tolist()

        if len(returns) < 30:
            warnings.append(f"Very few data points ({len(returns)}). Results may be unreliable.")

        start_date = df.index[0] if isinstance(df.index, pd.DatetimeIndex) and not df.empty else None
        end_date = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) and not df.empty else None

        start_dt = start_date.to_pydatetime() if start_date else None
        end_dt = end_date.to_pydatetime() if end_date else None

        return ReturnSeries(
            series_id=str(uuid.uuid4()),
            symbol=symbol,
            source_type=source_type,
            returns=ReturnSeriesBuilder.clean_returns(returns),
            start_date=start_dt,
            end_date=end_dt,
            frequency="1D",
            warnings=warnings
        )

    @staticmethod
    def from_portfolio_snapshot(snapshot: Any, data_by_symbol: dict[str, pd.DataFrame]) -> ReturnSeries:
        warnings = []
        returns_list = []

        # Calculate daily portfolio returns weighted by snapshot weights
        weights = {}
        if hasattr(snapshot, "items"):
            for item in snapshot.items:
                weights[item.symbol] = getattr(item, "weight_pct", 0) / 100.0

        if not weights:
            warnings.append("No items/weights found in snapshot.")
            return ReturnSeries(
                series_id=str(uuid.uuid4()),
                source_type=StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT,
                returns=[],
                frequency="1D",
                warnings=warnings
            )

        common_index = None
        returns_by_symbol = {}
        for sym, weight in weights.items():
            if sym in data_by_symbol and not data_by_symbol[sym].empty and "Close" in data_by_symbol[sym].columns:
                ret = data_by_symbol[sym]["Close"].pct_change().dropna()
                returns_by_symbol[sym] = ret * weight
                if common_index is None:
                    common_index = ret.index
                else:
                    common_index = common_index.intersection(ret.index)
            else:
                warnings.append(f"No price data available for {sym}.")

        if not common_index is None and not common_index.empty:
            portfolio_returns = pd.Series(0.0, index=common_index)
            for sym, ret in returns_by_symbol.items():
                portfolio_returns += ret.loc[common_index]
            returns_list = portfolio_returns.tolist()
        else:
            warnings.append("No common index found across symbols.")

        return ReturnSeries(
            series_id=str(uuid.uuid4()),
            source_type=StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT,
            returns=ReturnSeriesBuilder.clean_returns(returns_list),
            frequency="1D",
            warnings=warnings
        )

    @staticmethod
    def from_basket_simulation(result: Any) -> ReturnSeries:
        warnings = []
        returns = getattr(result, "daily_returns", [])
        if not returns:
            warnings.append("No daily returns found in basket simulation.")
        return ReturnSeries(
            series_id=str(uuid.uuid4()),
            source_type=StressInputType.BASKET_SIMULATION,
            returns=ReturnSeriesBuilder.clean_returns(returns),
            frequency="1D",
            warnings=warnings
        )

    @staticmethod
    def from_backtest_equity_curve(result: Any) -> ReturnSeries:
        warnings = []
        returns = []
        if hasattr(result, "equity_curve"):
            curve = result.equity_curve
            if isinstance(curve, pd.Series) or isinstance(curve, list):
                s = pd.Series(curve) if isinstance(curve, list) else curve
                returns = s.pct_change().dropna().tolist()
            else:
                warnings.append("Unknown equity_curve format.")
        else:
            warnings.append("No equity_curve found in backtest result.")

        return ReturnSeries(
            series_id=str(uuid.uuid4()),
            source_type=StressInputType.BACKTEST_EQUITY_CURVE,
            returns=ReturnSeriesBuilder.clean_returns(returns),
            frequency="1D",
            warnings=warnings
        )

    @staticmethod
    def from_paper_ledger(ledger: Any) -> ReturnSeries:
        warnings = ["Paper ledger conversion not fully implemented; returning mock empty series."]
        return ReturnSeries(
            series_id=str(uuid.uuid4()),
            source_type=StressInputType.PAPER_LEDGER,
            returns=[],
            frequency="1D",
            warnings=warnings
        )

    @staticmethod
    def clean_returns(returns: list[float]) -> list[float]:
        return [r for r in returns if not math.isnan(r) and not math.isinf(r)]

    @staticmethod
    def summary_stats(series: ReturnSeries) -> dict[str, Any]:
        ret = series.returns
        if not ret:
            return {"count": 0}

        arr = np.array(ret)
        return {
            "count": len(ret),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr))
        }
