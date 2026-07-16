import pandas as pd
from typing import Any, Protocol, List, Tuple
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from .models import (
    RiskContext, StopTargetReference, PositionSizeResult,
    RiskDecisionStatus, RiskRejectReason, RiskSide, RiskDecision, RiskFilterResult
)

class BaseRiskFilter(Protocol):
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        ...

class SignalScoreFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        if signal.score < settings.RISK_MIN_SIGNAL_SCORE:
            rejects.append(RiskRejectReason.SCORE_TOO_LOW)
        if signal.confidence < settings.RISK_MIN_CONFIDENCE:
            rejects.append(RiskRejectReason.CONFIDENCE_TOO_LOW)
        return rejects, []

class RiskRewardFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        warnings = []
        rr = stop_target.risk_reward if stop_target else None
        if rr is not None:
            if rr < settings.RISK_MIN_RISK_REWARD:
                rejects.append(RiskRejectReason.RISK_REWARD_TOO_LOW)
        else:
            if settings.RISK_REJECT_IF_NO_TARGET and (not stop_target or not stop_target.target_price):
                rejects.append(RiskRejectReason.TARGET_INVALID)
            else:
                warnings.append("No valid risk/reward calculated.")

        if settings.RISK_REJECT_IF_NO_STOP and (not stop_target or not stop_target.stop_price):
            rejects.append(RiskRejectReason.STOP_INVALID)

        return rejects, warnings

class PositionLimitsFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        if position_size:
            if position_size.final_position_pct > settings.RISK_MAX_POSITION_SIZE_PCT + 0.0001:
                rejects.append(RiskRejectReason.MAX_POSITION_LIMIT_EXCEEDED)
            if position_size.quantity <= 0:
                rejects.append(RiskRejectReason.POSITION_TOO_SMALL)
        return rejects, []

class PortfolioLimitsFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        if position_size and position_size.risk_pct is not None:
            proposed_risk = position_size.risk_pct
            if context.portfolio_risk_pct + proposed_risk > settings.RISK_MAX_PORTFOLIO_RISK_PCT + 0.0001:
                rejects.append(RiskRejectReason.PORTFOLIO_RISK_LIMIT_EXCEEDED)

        if context.daily_signal_count >= settings.RISK_MAX_DAILY_SIGNALS:
            rejects.append(RiskRejectReason.DAILY_SIGNAL_LIMIT_EXCEEDED)

        if context.open_position_count >= settings.RISK_MAX_OPEN_POSITIONS:
            rejects.append(RiskRejectReason.MAX_POSITION_LIMIT_EXCEEDED)

        if not settings.RISK_ALLOW_SAME_SYMBOL_POSITION:
            if signal.symbol in context.current_positions:
                rejects.append(RiskRejectReason.SYMBOL_ALREADY_HELD)
        return rejects, []

class LiquidityFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        turnover = signal.feature_snapshot.get("avg_turnover_20")
        if turnover is None and data is not None and not data.empty and "volume" in data.columns and "close" in data.columns:
            turnover = (data["volume"] * data["close"]).rolling(20).mean().iloc[-1]

        if turnover is not None and turnover < settings.RISK_MIN_AVG_TURNOVER_TRY:
            rejects.append(RiskRejectReason.LIQUIDITY_TOO_LOW)
        return rejects, []

class VolatilityFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        vol_score = signal.feature_snapshot.get("volatility_risk_score")
        if vol_score is not None and vol_score > settings.RISK_MAX_VOLATILITY_PCT * 100:
            rejects.append(RiskRejectReason.VOLATILITY_TOO_HIGH)
        else:
            atr_pct = signal.feature_snapshot.get("atr_pct_14")
            if atr_pct is not None and atr_pct > settings.RISK_MAX_ATR_PCT:
                rejects.append(RiskRejectReason.VOLATILITY_TOO_HIGH)
        return rejects, []

class CostFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        if position_size and position_size.estimated_cost is not None and position_size.final_notional > 0:
            cost_bps = (position_size.estimated_cost / position_size.final_notional) * 10000
            if cost_bps > settings.RISK_MAX_COST_BPS:
                rejects.append(RiskRejectReason.COST_TOO_HIGH)
        return rejects, []

class SideFilter:
    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None, settings: Settings) -> Tuple[List[RiskRejectReason], List[str]]:
        rejects = []
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)
        if side == RiskSide.SHORT and not settings.RISK_ALLOW_SHORT:
            rejects.append(RiskRejectReason.UNKNOWN)
        return rejects, []

class RiskFilterEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.filters: List[BaseRiskFilter] = [
            SignalScoreFilter(),
            RiskRewardFilter(),
            PositionLimitsFilter(),
            PortfolioLimitsFilter(),
            LiquidityFilter(),
            VolatilityFilter(),
            CostFilter(),
            SideFilter()
        ]

    def apply_regime_stress_filter(self, decision: RiskDecision) -> RiskDecision:
        if decision.status == RiskDecisionStatus.REJECTED:
            return decision

        use_regime = getattr(self.settings, "RISK_USE_REGIME_FILTER", False)
        if not use_regime:
            return decision

        metadata = decision.signal.metadata or {}
        market_regime = metadata.get("market_regime")
        volatility_regime = metadata.get("volatility_regime")

        if not market_regime or not volatility_regime:
            return decision

        is_stress = (volatility_regime == "STRESS") or (market_regime == "HIGH_VOLATILITY_STRESS")

        if is_stress:
            reject_stress = getattr(self.settings, "RISK_REJECT_STRESS_REGIME", False)
            if reject_stress:
                decision.status = RiskDecisionStatus.REJECTED
                decision.reasons.append("Rejected by RegimeStressFilter: Volatility is at STRESS levels.")
                decision.position_size = 0.0
                decision.position_value = 0.0
                return decision

            reduce_stress = getattr(self.settings, "RISK_REDUCE_IN_STRESS_REGIME", True)
            if reduce_stress:
                if decision.position_size and decision.position_size > 0:
                    decision.position_size = max(1.0, decision.position_size * 0.5)
                    decision.position_value = decision.position_size * decision.signal.price
                    decision.reasons.append("RegimeStressFilter: Position size reduced by 50% due to STRESS regime.")
                    decision.status = RiskDecisionStatus.APPROVED

        return decision

    def score_adjustment_from_risk(self, warnings: list[str]) -> float:
        return -2.0 * len(warnings)

    def evaluate(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, position_size: PositionSizeResult | None, data: pd.DataFrame | None = None) -> RiskFilterResult:
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        if side == RiskSide.FLAT:
            return RiskFilterResult(passed=False, status=RiskDecisionStatus.WATCH_ONLY, reject_reasons=[], warnings=[])

        all_reject_reasons = []
        all_warnings = []

        for f in self.filters:
            rejects, warnings = f.evaluate(signal, context, stop_target, position_size, data, self.settings)
            all_reject_reasons.extend(rejects)
            all_warnings.extend(warnings)

        passed = len(all_reject_reasons) == 0
        status = RiskDecisionStatus.APPROVED if passed else RiskDecisionStatus.REJECTED

        if passed and position_size and position_size.reduced:
            status = RiskDecisionStatus.REDUCED

        adj = self.score_adjustment_from_risk(all_warnings)

        return RiskFilterResult(
            passed=passed,
            status=status,
            reject_reasons=list(set(all_reject_reasons)),
            warnings=all_warnings,
            score_adjustment=adj
        )

class MLScoreFilter:
    def evaluate(self, candidate) -> Any:

        use_ml = getattr(self.settings, "RISK_USE_ML_FILTER", False)
        if not use_ml:
            return RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED)

        reject_missing = getattr(self.settings, "RISK_REJECT_IF_ML_MISSING", False)

        if "ml_prediction_score" not in candidate.metadata:
            if reject_missing:
                return RiskFilterResult(passed=False, status=RiskDecisionStatus.REJECTED, reject_reasons=[RiskRejectReason.UNKNOWN], warnings=["ML score missing but required by risk filter"])
            return RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED, warnings=["ML score missing, but not strictly required"])

        score = candidate.metadata["ml_prediction_score"]
        prob = candidate.metadata.get("ml_probability_positive")
        min_score = getattr(self.settings, "RISK_MIN_ML_SCORE", 50.0)
        min_prob = getattr(self.settings, "RISK_MIN_ML_PROBABILITY_POSITIVE", 0.55)

        if score < min_score:
            return RiskFilterResult(passed=False, status=RiskDecisionStatus.REJECTED, reject_reasons=[RiskRejectReason.SCORE_TOO_LOW], warnings=[f"ML Score {score} < {min_score}"])
        if prob is not None and prob < min_prob:
            return RiskFilterResult(passed=False, status=RiskDecisionStatus.REJECTED, reject_reasons=[RiskRejectReason.CONFIDENCE_TOO_LOW], warnings=[f"ML Probability {prob} < {min_prob}"])

        return RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED, warnings=["ML Risk Filter Passed"])
