import pandas as pd
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from .models import StopMethod, RiskSide
from bist_signal_bot.core.exceptions import StopModelError

class StopModel:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def calculate_stop(self, signal: SignalCandidate, data: pd.DataFrame | None = None, method: StopMethod | None = None) -> float | None:
        method = method or StopMethod(self.settings.RISK_STOP_METHOD)
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        if side == RiskSide.FLAT:
            return None

        entry = signal.entry_reference_price
        if not entry or entry <= 0:
            raise StopModelError("Entry reference price is required to calculate stop")

        if method == StopMethod.NONE:
            return None

        if method == StopMethod.FIXED_PERCENT:
            pct = self.settings.RISK_FIXED_STOP_PCT
            return entry * (1 - pct) if side == RiskSide.LONG else entry * (1 + pct)

        if method == StopMethod.ATR_MULTIPLE:
            atr = None
            if "atr_14" in signal.feature_snapshot and signal.feature_snapshot["atr_14"]:
                atr = signal.feature_snapshot["atr_14"]
            elif data is not None and not data.empty and "atr_14" in data.columns:
                atr = data.iloc[-1]["atr_14"]
            elif data is not None and not data.empty and "atr_pct_14" in data.columns:
                atr = data.iloc[-1]["atr_pct_14"] * entry

            if not atr or atr <= 0:
                pct = self.settings.RISK_FIXED_STOP_PCT
                return entry * (1 - pct) if side == RiskSide.LONG else entry * (1 + pct)

            mult = self.settings.RISK_ATR_MULTIPLIER
            return entry - (atr * mult) if side == RiskSide.LONG else entry + (atr * mult)

        if method == StopMethod.RECENT_SWING:
            if data is None or data.empty:
                pct = self.settings.RISK_FIXED_STOP_PCT
                return entry * (1 - pct) if side == RiskSide.LONG else entry * (1 + pct)

            lookback = self.settings.RISK_SWING_LOOKBACK
            recent_data = data.tail(lookback)
            if side == RiskSide.LONG:
                stop = recent_data["low"].min()
            else:
                stop = recent_data["high"].max()

            if not self.validate_stop(entry, stop, side):
                pct = self.settings.RISK_FIXED_STOP_PCT
                return entry * (1 - pct) if side == RiskSide.LONG else entry * (1 + pct)
            return stop

        if method == StopMethod.VOLATILITY_BASED:
            vol = None
            if "hist_vol_20" in signal.feature_snapshot and signal.feature_snapshot["hist_vol_20"]:
                vol = signal.feature_snapshot["hist_vol_20"]

            if not vol or vol <= 0:
                pct = self.settings.RISK_FIXED_STOP_PCT
                return entry * (1 - pct) if side == RiskSide.LONG else entry * (1 + pct)

            daily_vol_pct = vol / (252 ** 0.5)
            stop_dist_pct = daily_vol_pct * self.settings.RISK_ATR_MULTIPLIER
            return entry * (1 - stop_dist_pct) if side == RiskSide.LONG else entry * (1 + stop_dist_pct)

        return None

    def validate_stop(self, entry: float, stop: float | None, side: RiskSide) -> bool:
        if stop is None:
            return True
        if stop <= 0:
            return False
        if side == RiskSide.LONG and stop >= entry:
            return False
        if side == RiskSide.SHORT and stop <= entry:
            return False
        return True
