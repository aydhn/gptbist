import pandas as pd
from typing import Any
from bist_signal_bot.portfolio_research.models import (
    CorrelationPair,
    PortfolioConstraintStatus
)

class PortfolioCorrelationAnalyzer:

    def calculate_correlations(self, data_by_symbol: dict[str, pd.DataFrame], lookback_days: int = 120) -> list[CorrelationPair]:
        series_dict = {}
        for sym, df in data_by_symbol.items():
            series_dict[sym] = self.returns_series(df, lookback_days)

        if not series_dict:
            return []

        combined = pd.DataFrame(series_dict)
        corr_matrix = combined.corr()

        pairs = []
        symbols = list(corr_matrix.columns)
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                sym_a = symbols[i]
                sym_b = symbols[j]
                val = corr_matrix.iloc[i, j]
                if pd.isna(val):
                    continue
                pairs.append(CorrelationPair(
                    symbol_a=sym_a,
                    symbol_b=sym_b,
                    correlation=float(val),
                    lookback_days=lookback_days
                ))
        return pairs

    def returns_series(self, df: pd.DataFrame, lookback_days: int) -> pd.Series:
        if df is None or df.empty or 'close' not in df.columns:
            return pd.Series(dtype=float)
        # Avoid mutating input dataframe
        close = df['close'].copy()
        returns = close.pct_change().dropna()
        if len(returns) > lookback_days:
            returns = returns.iloc[-lookback_days:]
        return returns

    def high_correlation_warnings(self, pairs: list[CorrelationPair], threshold: float = 0.80) -> list[str]:
        warnings = []
        for p in pairs:
            if p.correlation >= threshold:
                warnings.append(f"High correlation ({p.correlation:.2f}) between {p.symbol_a} and {p.symbol_b}")
                p.status = PortfolioConstraintStatus.WARN
                p.warning = "Correlation exceeds threshold"
            elif p.correlation <= -threshold:
                warnings.append(f"High negative correlation ({p.correlation:.2f}) between {p.symbol_a} and {p.symbol_b}")
        return warnings

    def correlation_penalty(self, symbol: str, pairs: list[CorrelationPair]) -> float:
        penalty = 0.0
        for p in pairs:
            if (p.symbol_a == symbol or p.symbol_b == symbol) and p.correlation > 0.5:
                penalty += (p.correlation - 0.5) * 0.1
        return min(penalty, 0.5)
