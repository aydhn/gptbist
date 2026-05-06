import pandas as pd
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from .models import (
    RiskContext, StopTargetReference, PositionSizeResult, RiskFilterResult,
    RiskDecisionStatus, RiskRejectReason, RiskSide
)

class RiskFilterEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def score_adjustment_from_risk(self, warnings: list[str]) -> float:
        return -2.0 * len(warnings)

    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None = None) -> RiskFilterResult:
        reject_reasons = []
        warnings = []
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        if side == RiskSide.FLAT:
            return RiskFilterResult(passed=False, status=RiskDecisionStatus.WATCH_ONLY, reject_reasons=[], warnings=[])

        if signal.score < self.settings.RISK_MIN_SIGNAL_SCORE:
            reject_reasons.append(RiskRejectReason.SCORE_TOO_LOW)

        if signal.confidence < self.settings.RISK_MIN_CONFIDENCE:
            reject_reasons.append(RiskRejectReason.CONFIDENCE_TOO_LOW)

        rr = stop_target.risk_reward if stop_target else None
        if rr is not None:
            if rr < self.settings.RISK_MIN_RISK_REWARD:
                reject_reasons.append(RiskRejectReason.RISK_REWARD_TOO_LOW)
        else:
            if self.settings.RISK_REJECT_IF_NO_TARGET and not stop_target.target_price:
                reject_reasons.append(RiskRejectReason.TARGET_INVALID)
            else:
                warnings.append("No valid risk/reward calculated.")

        if self.settings.RISK_REJECT_IF_NO_STOP and stop_target and not stop_target.stop_price:
            reject_reasons.append(RiskRejectReason.STOP_INVALID)

        if position_size:
            if position_size.final_position_pct > self.settings.RISK_MAX_POSITION_SIZE_PCT + 0.0001:
                reject_reasons.append(RiskRejectReason.MAX_POSITION_LIMIT_EXCEEDED)
            if position_size.quantity <= 0:
                reject_reasons.append(RiskRejectReason.POSITION_TOO_SMALL)

        if position_size and position_size.risk_pct is not None:
            proposed_risk = position_size.risk_pct
            if context.portfolio_risk_pct + proposed_risk > self.settings.RISK_MAX_PORTFOLIO_RISK_PCT + 0.0001:
                reject_reasons.append(RiskRejectReason.PORTFOLIO_RISK_LIMIT_EXCEEDED)

        if context.daily_signal_count >= self.settings.RISK_MAX_DAILY_SIGNALS:
            reject_reasons.append(RiskRejectReason.DAILY_SIGNAL_LIMIT_EXCEEDED)

        if context.open_position_count >= self.settings.RISK_MAX_OPEN_POSITIONS:
            reject_reasons.append(RiskRejectReason.MAX_POSITION_LIMIT_EXCEEDED)

        if not self.settings.RISK_ALLOW_SAME_SYMBOL_POSITION:
            if signal.symbol in context.current_positions:
                reject_reasons.append(RiskRejectReason.SYMBOL_ALREADY_HELD)

        turnover = signal.feature_snapshot.get("avg_turnover_20")
        if turnover is None and data is not None and not data.empty and "volume" in data.columns and "close" in data.columns:
            turnover = (data["volume"] * data["close"]).rolling(20).mean().iloc[-1]

        if turnover is not None and turnover < self.settings.RISK_MIN_AVG_TURNOVER_TRY:
            reject_reasons.append(RiskRejectReason.LIQUIDITY_TOO_LOW)

        vol_score = signal.feature_snapshot.get("volatility_risk_score")
        if vol_score is not None and vol_score > self.settings.RISK_MAX_VOLATILITY_PCT * 100:
            reject_reasons.append(RiskRejectReason.VOLATILITY_TOO_HIGH)
        else:
            atr_pct = signal.feature_snapshot.get("atr_pct_14")
            if atr_pct is not None and atr_pct > self.settings.RISK_MAX_ATR_PCT:
                reject_reasons.append(RiskRejectReason.VOLATILITY_TOO_HIGH)

        if position_size and position_size.estimated_cost is not None and position_size.final_notional > 0:
            cost_bps = (position_size.estimated_cost / position_size.final_notional) * 10000
            if cost_bps > self.settings.RISK_MAX_COST_BPS:
                reject_reasons.append(RiskRejectReason.COST_TOO_HIGH)

        if side == RiskSide.SHORT and not self.settings.RISK_ALLOW_SHORT:
            reject_reasons.append(RiskRejectReason.UNKNOWN)

        passed = len(reject_reasons) == 0
        status = RiskDecisionStatus.APPROVED if passed else RiskDecisionStatus.REJECTED

        if passed and position_size and position_size.reduced:
            status = RiskDecisionStatus.REDUCED

        adj = self.score_adjustment_from_risk(warnings)

        return RiskFilterResult(
            passed=passed,
            status=status,
            reject_reasons=list(set(reject_reasons)),
            warnings=warnings,
            score_adjustment=adj
        )
