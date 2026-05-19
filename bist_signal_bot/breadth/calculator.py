from datetime import datetime
import pandas as pd
import numpy as np

from bist_signal_bot.breadth.models import BreadthAnalysisRequest, BreadthSnapshot, BreadthStatus

class BreadthCalculator:
    def __init__(self, settings=None):
        self.settings = settings

    def _filter_df_by_date(self, df: pd.DataFrame, as_of_date: datetime) -> pd.DataFrame:
        if "date" not in df.columns:
            return df

        filtered = df[df["date"] <= pd.Timestamp(as_of_date)].copy()
        if not filtered.empty:
            filtered = filtered.sort_values("date").reset_index(drop=True)
        return filtered

    def calculate_snapshot(self, data_by_symbol: dict[str, pd.DataFrame], request: BreadthAnalysisRequest) -> BreadthSnapshot:
        import uuid
        as_of_date = request.as_of_date or datetime.now()

        advance_decline = self.calculate_advance_decline(data_by_symbol, as_of_date)

        pct_above = {}
        for w in [20, 50, 100, 200]:
            pct_above[str(w)] = self.percent_above_ma(data_by_symbol, w, as_of_date)

        nh_nl = {}
        nl_count = {}
        for w in [20, 252]:
            h, l = self.new_high_low_counts(data_by_symbol, w, as_of_date)
            nh_nl[str(w)] = h
            nl_count[str(w)] = l

        snapshot = BreadthSnapshot(
            snapshot_id=str(uuid.uuid4()),
            as_of_date=as_of_date,
            universe_name=request.universe_name,
            symbols=request.symbols,
            benchmark_symbol=request.benchmark_symbol,
            advance_count=advance_decline.get("advance", 0),
            decline_count=advance_decline.get("decline", 0),
            unchanged_count=advance_decline.get("unchanged", 0),
            percent_above_ma=pct_above,
            new_high_count=nh_nl,
            new_low_count=nl_count,
            volume_breadth_score=self.volume_breadth(data_by_symbol, as_of_date),
            momentum_breadth_score=self.momentum_breadth(data_by_symbol, 20, as_of_date),
            composite_score=50.0, # Dummy composite
            status=BreadthStatus.NEUTRAL
        )
        return snapshot

    def calculate_advance_decline(self, data_by_symbol: dict[str, pd.DataFrame], as_of_date: datetime) -> dict[str, int]:
        adv, dec, unch = 0, 0, 0
        for sym, df in data_by_symbol.items():
            fdf = self._filter_df_by_date(df, as_of_date)
            if len(fdf) >= 2:
                last_close = fdf.iloc[-1]["close"]
                prev_close = fdf.iloc[-2]["close"]
                if last_close > prev_close:
                    adv += 1
                elif last_close < prev_close:
                    dec += 1
                else:
                    unch += 1
        return {"advance": adv, "decline": dec, "unchanged": unch}

    def percent_above_ma(self, data_by_symbol: dict[str, pd.DataFrame], window: int, as_of_date: datetime) -> float:
        above = 0
        total = 0
        for sym, df in data_by_symbol.items():
            fdf = self._filter_df_by_date(df, as_of_date)
            if len(fdf) >= window:
                ma = fdf["close"].rolling(window).mean().iloc[-1]
                last_close = fdf["close"].iloc[-1]
                if pd.notna(ma) and last_close > ma:
                    above += 1
                total += 1
        return (above / total * 100) if total > 0 else 0.0

    def new_high_low_counts(self, data_by_symbol: dict[str, pd.DataFrame], window: int, as_of_date: datetime) -> tuple[int, int]:
        nh, nl = 0, 0
        for sym, df in data_by_symbol.items():
            fdf = self._filter_df_by_date(df, as_of_date)
            if len(fdf) >= window:
                recent = fdf.iloc[-window:]
                high_max = recent["high"].max() if "high" in recent.columns else recent["close"].max()
                low_min = recent["low"].min() if "low" in recent.columns else recent["close"].min()
                last_high = fdf.iloc[-1]["high"] if "high" in fdf.columns else fdf.iloc[-1]["close"]
                last_low = fdf.iloc[-1]["low"] if "low" in fdf.columns else fdf.iloc[-1]["close"]

                if last_high >= high_max:
                    nh += 1
                if last_low <= low_min:
                    nl += 1
        return nh, nl

    def volume_breadth(self, data_by_symbol: dict[str, pd.DataFrame], as_of_date: datetime) -> float | None:
        adv_vol = 0
        dec_vol = 0
        for sym, df in data_by_symbol.items():
            fdf = self._filter_df_by_date(df, as_of_date)
            if len(fdf) >= 2 and "volume" in fdf.columns:
                last_close = fdf.iloc[-1]["close"]
                prev_close = fdf.iloc[-2]["close"]
                vol = fdf.iloc[-1]["volume"]
                if last_close > prev_close:
                    adv_vol += vol
                elif last_close < prev_close:
                    dec_vol += vol
        total = adv_vol + dec_vol
        return (adv_vol / total * 100) if total > 0 else None

    def momentum_breadth(self, data_by_symbol: dict[str, pd.DataFrame], window: int, as_of_date: datetime) -> float | None:
        pos = 0
        total = 0
        for sym, df in data_by_symbol.items():
            fdf = self._filter_df_by_date(df, as_of_date)
            if len(fdf) > window:
                last_close = fdf.iloc[-1]["close"]
                past_close = fdf.iloc[-(window+1)]["close"]
                if last_close > past_close:
                    pos += 1
                total += 1
        return (pos / total * 100) if total > 0 else None

    def composite_score(self, metrics: list) -> float:
        return 50.0
