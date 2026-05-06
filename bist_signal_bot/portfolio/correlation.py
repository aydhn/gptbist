import logging
from typing import Optional
from datetime import datetime
import pandas as pd
import numpy as np

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio.models import CorrelationMatrixResult

class CorrelationAnalyzer:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        from bist_signal_bot.config.settings import settings as default_settings
        self.settings = settings or default_settings
        self.logger = logger or logging.getLogger(__name__)

    def calculate_returns_matrix(
        self,
        price_data_by_symbol: dict[str, pd.DataFrame],
        price_col: str = "close",
        lookback_rows: int = 60
    ) -> pd.DataFrame:
        if not price_data_by_symbol:
            return pd.DataFrame()

        returns_dict = {}
        for sym, df in price_data_by_symbol.items():
            if df.empty or price_col not in df.columns:
                continue

            # Use only the last lookback_rows
            tail_df = df.tail(lookback_rows + 1)
            returns = tail_df[price_col].pct_change().dropna()
            returns_dict[sym] = returns

        if not returns_dict:
            return pd.DataFrame()

        # Align indexes
        returns_df = pd.DataFrame(returns_dict)
        return returns_df

    def calculate_correlation_matrix(
        self,
        price_data_by_symbol: dict[str, pd.DataFrame],
        method: str = "pearson",
        lookback_rows: int = 60
    ) -> CorrelationMatrixResult:
        issues = []

        if not price_data_by_symbol:
            issues.append("No price data provided")
            return CorrelationMatrixResult(
                symbols=[],
                matrix=pd.DataFrame(),
                lookback_rows=lookback_rows,
                method=method,
                generated_at=datetime.utcnow(),
                issues=issues,
                metadata={}
            )

        returns_df = self.calculate_returns_matrix(price_data_by_symbol, lookback_rows=lookback_rows)

        if returns_df.empty:
            issues.append("Could not compute valid returns matrix")
            return CorrelationMatrixResult(
                symbols=list(price_data_by_symbol.keys()),
                matrix=pd.DataFrame(),
                lookback_rows=lookback_rows,
                method=method,
                generated_at=datetime.utcnow(),
                issues=issues,
                metadata={}
            )

        # Drop columns with all NaNs or single unique value to prevent warnings
        returns_df = returns_df.dropna(axis=1, how='all')

        valid_symbols = list(returns_df.columns)
        missing_symbols = set(price_data_by_symbol.keys()) - set(valid_symbols)
        if missing_symbols:
            issues.append(f"Missing valid returns for symbols: {missing_symbols}")

        corr_matrix = returns_df.corr(method=method)

        return CorrelationMatrixResult(
            symbols=valid_symbols,
            matrix=corr_matrix,
            lookback_rows=lookback_rows,
            method=method,
            generated_at=datetime.utcnow(),
            issues=issues,
            metadata={"missing_symbols": list(missing_symbols)}
        )

    def max_pairwise_correlation(self, symbol: str, existing_symbols: list[str], corr: CorrelationMatrixResult) -> Optional[float]:
        if corr.matrix.empty or symbol not in corr.matrix.columns:
            return None

        max_corr = None
        for ex_sym in existing_symbols:
            if ex_sym in corr.matrix.columns and ex_sym != symbol:
                val = corr.matrix.loc[symbol, ex_sym]
                if pd.notna(val):
                    if max_corr is None or val > max_corr:
                        max_corr = float(val)

        return max_corr

    def average_portfolio_correlation(self, symbols: list[str], corr: CorrelationMatrixResult) -> Optional[float]:
        if corr.matrix.empty:
            return None

        valid_symbols = [s for s in symbols if s in corr.matrix.columns]
        if len(valid_symbols) < 2:
            return None

        sub_matrix = corr.matrix.loc[valid_symbols, valid_symbols]

        # Upper triangle without diagonal
        mask = np.triu(np.ones(sub_matrix.shape, dtype=bool), k=1)
        vals = sub_matrix.where(mask).values.flatten()
        vals = vals[~np.isnan(vals)]

        if len(vals) == 0:
            return None

        return float(np.mean(vals))

    def correlation_warnings(
        self,
        candidate_symbols: list[str],
        existing_symbols: list[str],
        corr: CorrelationMatrixResult,
        threshold: float
    ) -> list[str]:
        warnings = []
        if corr.matrix.empty:
            warnings.append("Correlation matrix is empty, correlation checks bypassed")
            return warnings

        for c_sym in candidate_symbols:
            if c_sym not in corr.matrix.columns:
                warnings.append(f"No correlation data for candidate {c_sym}")
                continue

            max_c = self.max_pairwise_correlation(c_sym, existing_symbols, corr)
            if max_c is not None and max_c > threshold:
                warnings.append(f"Candidate {c_sym} has high correlation ({max_c:.2f}) with existing portfolio > {threshold}")

        return warnings
