from datetime import datetime
import pandas as pd
import numpy as np
from typing import Any

from bist_signal_bot.breadth.models import RelativeStrengthScore

class RelativeStrengthCalculator:
    def __init__(self, settings=None):
        self.settings = settings

    def _filter_df_by_date(self, df: pd.DataFrame, as_of_date: datetime) -> pd.DataFrame:
        if "date" not in df.columns:
            return df
        filtered = df[df["date"] <= pd.Timestamp(as_of_date)].copy()
        if not filtered.empty:
            filtered = filtered.sort_values("date").reset_index(drop=True)
        return filtered

    def relative_return(self, symbol_df: pd.DataFrame, benchmark_df: pd.DataFrame | None, window: int, as_of_date: datetime) -> float | None:
        sym_fdf = self._filter_df_by_date(symbol_df, as_of_date)
        if len(sym_fdf) <= window:
            return None

        sym_last = sym_fdf["close"].iloc[-1]
        sym_past = sym_fdf["close"].iloc[-(window+1)]
        sym_ret = (sym_last - sym_past) / sym_past

        if benchmark_df is not None:
            bench_fdf = self._filter_df_by_date(benchmark_df, as_of_date)
            if len(bench_fdf) > window:
                bench_last = bench_fdf["close"].iloc[-1]
                bench_past = bench_fdf["close"].iloc[-(window+1)]
                bench_ret = (bench_last - bench_past) / bench_past
                return (sym_ret - bench_ret) * 100

        return sym_ret * 100

    def absolute_momentum(self, symbol_df: pd.DataFrame, window: int, as_of_date: datetime) -> float | None:
        sym_fdf = self._filter_df_by_date(symbol_df, as_of_date)
        if len(sym_fdf) <= window:
            return None
        sym_last = sym_fdf["close"].iloc[-1]
        sym_past = sym_fdf["close"].iloc[-(window+1)]
        return ((sym_last - sym_past) / sym_past) * 100

    def calculate_scores(self, data_by_symbol: dict[str, pd.DataFrame], benchmark_data: pd.DataFrame | None, sectors: dict[str, str] | None, as_of_date: datetime) -> list[RelativeStrengthScore]:
        scores = []
        sectors = sectors or {}

        for symbol, df in data_by_symbol.items():
            rs20 = self.relative_return(df, benchmark_data, 20, as_of_date)
            rs50 = self.relative_return(df, benchmark_data, 50, as_of_date)
            rs100 = self.relative_return(df, benchmark_data, 100, as_of_date)
            rs200 = self.relative_return(df, benchmark_data, 200, as_of_date)
            abs_mom = self.absolute_momentum(df, 50, as_of_date)

            comp = self.composite_rs_score(rs20, rs50, rs100, rs200, abs_mom)

            score = RelativeStrengthScore(
                symbol=symbol,
                benchmark_symbol="XU100" if benchmark_data is not None else None,
                sector=sectors.get(symbol),
                as_of_date=as_of_date,
                rs_20=rs20,
                rs_50=rs50,
                rs_100=rs100,
                rs_200=rs200,
                absolute_momentum_score=abs_mom,
                composite_score=comp
            )
            scores.append(score)

        return self.percentile_rank_scores(scores)

    def composite_rs_score(self, rs_20, rs_50, rs_100, rs_200, absolute_momentum_score) -> float:
        valid_rs = [x for x in [rs_20, rs_50, rs_100, rs_200] if x is not None]
        if not valid_rs:
            return 50.0

        # dummy score: average of relative returns scaled and clamped to 0-100
        avg_rs = sum(valid_rs) / len(valid_rs)
        score = 50.0 + (avg_rs * 2.0)
        return max(0.0, min(100.0, score))

    def percentile_rank_scores(self, scores: list[RelativeStrengthScore]) -> list[RelativeStrengthScore]:
        if not scores:
            return scores

        comps = [s.composite_score for s in scores]
        n = len(comps)
        for s in scores:
            c = sum(1 for x in comps if x < s.composite_score)
            s.percentile_rank = (c / n) * 100 if n > 0 else 50.0
        return scores
