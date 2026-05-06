import pandas as pd
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from .models import TargetMethod, StopMethod, RiskSide, StopTargetReference
from bist_signal_bot.core.exceptions import TargetModelError

class TargetModel:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def calculate_target(self, signal: SignalCandidate, stop_price: float | None, data: pd.DataFrame | None = None, method: TargetMethod | None = None) -> float | None:
        method = method or TargetMethod(self.settings.RISK_TARGET_METHOD)
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        if side == RiskSide.FLAT:
            return None

        entry = signal.entry_reference_price
        if not entry or entry <= 0:
            raise TargetModelError("Entry reference price is required to calculate target")

        if method == TargetMethod.NONE:
            return None

        if method == TargetMethod.FIXED_PERCENT:
            pct = self.settings.RISK_FIXED_TARGET_PCT
            return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)

        if method == TargetMethod.RISK_REWARD_MULTIPLE:
            if not stop_price:
                pct = self.settings.RISK_FIXED_TARGET_PCT
                return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)

            risk_per_share = entry - stop_price if side == RiskSide.LONG else stop_price - entry
            if risk_per_share <= 0:
                pct = self.settings.RISK_FIXED_TARGET_PCT
                return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)

            mult = self.settings.RISK_TARGET_R_MULTIPLE
            return entry + (risk_per_share * mult) if side == RiskSide.LONG else entry - (risk_per_share * mult)

        if method == TargetMethod.ATR_MULTIPLE:
            atr = None
            if "atr_14" in signal.feature_snapshot and signal.feature_snapshot["atr_14"]:
                atr = signal.feature_snapshot["atr_14"]
            elif data is not None and not data.empty and "atr_14" in data.columns:
                atr = data.iloc[-1]["atr_14"]

            if not atr or atr <= 0:
                pct = self.settings.RISK_FIXED_TARGET_PCT
                return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)

            dist = atr * self.settings.RISK_ATR_MULTIPLIER * self.settings.RISK_TARGET_R_MULTIPLE
            return entry + dist if side == RiskSide.LONG else entry - dist

        if method == TargetMethod.RECENT_RESISTANCE_SUPPORT:
            if data is None or data.empty:
                pct = self.settings.RISK_FIXED_TARGET_PCT
                return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)

            lookback = self.settings.RISK_SWING_LOOKBACK
            recent_data = data.tail(lookback)
            if side == RiskSide.LONG:
                target = recent_data["high"].max()
            else:
                target = recent_data["low"].min()

            if not self.validate_target(entry, target, side):
                pct = self.settings.RISK_FIXED_TARGET_PCT
                return entry * (1 + pct) if side == RiskSide.LONG else entry * (1 - pct)
            return target

        return None

    def validate_target(self, entry: float, target: float | None, side: RiskSide) -> bool:
        if target is None:
            return True
        if target <= 0:
            return False
        if side == RiskSide.LONG and target <= entry:
            return False
        if side == RiskSide.SHORT and target >= entry:
            return False
        return True

    def build_stop_target_reference(self, signal: SignalCandidate, stop_price: float | None, target_price: float | None, stop_method: StopMethod, target_method: TargetMethod) -> StopTargetReference:
        entry = signal.entry_reference_price
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        risk_per_share = None
        if stop_price and self.validate_target(entry, stop_price, RiskSide.SHORT if side == RiskSide.LONG else RiskSide.LONG):
             risk_per_share = entry - stop_price if side == RiskSide.LONG else stop_price - entry

        reward_per_share = None
        if target_price:
             reward_per_share = target_price - entry if side == RiskSide.LONG else entry - target_price

        risk_reward = None
        if risk_per_share and risk_per_share > 0 and reward_per_share and reward_per_share > 0:
             risk_reward = reward_per_share / risk_per_share

        return StopTargetReference(
            entry_price=entry,
            stop_price=stop_price,
            target_price=target_price,
            risk_per_share=max(0, risk_per_share) if risk_per_share is not None else None,
            reward_per_share=max(0, reward_per_share) if reward_per_share is not None else None,
            risk_reward=max(0, risk_reward) if risk_reward is not None else None,
            stop_method=stop_method,
            target_method=target_method
        )
