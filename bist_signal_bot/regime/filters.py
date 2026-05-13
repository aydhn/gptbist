import logging
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.regime.models import (
    RegimeClassification, RegimeConfig, RegimeFilterResult,
    RegimeFilterDecision, RegimeScoreMode, MarketRegime, VolatilityRegime, LiquidityRegime
)

class RegimeSignalFilter:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def _determine_decision(self, signal: SignalCandidate, regime: RegimeClassification, config: RegimeConfig) -> tuple[RegimeFilterDecision, float, list[str]]:
        decision = RegimeFilterDecision.PASS
        reduction_factor = 1.0
        reasons = []

        if config.mode == RegimeScoreMode.METADATA_ONLY:
            return decision, reduction_factor, ["Metadata only mode active"]

        is_long = signal.direction == SignalDirection.LONG

        if regime.market_regime == MarketRegime.HIGH_VOLATILITY_STRESS or regime.volatility_regime == VolatilityRegime.STRESS:
            if config.reject_stress_regime:
                decision = RegimeFilterDecision.REJECT
                reasons.append("Rejected due to stress regime.")
            elif config.reduce_in_stress:
                decision = RegimeFilterDecision.REDUCE
                reduction_factor = config.stress_reduction_factor
                reasons.append(f"Reduced by factor {reduction_factor} due to stress regime.")

        if regime.liquidity_regime == LiquidityRegime.ILLIQUID:
            decision = RegimeFilterDecision.REJECT
            reasons.append("Rejected due to illiquid market conditions.")

        if decision == RegimeFilterDecision.PASS:
            if is_long and regime.market_regime in (MarketRegime.TRENDING_DOWN, MarketRegime.RISK_OFF):
                if config.min_regime_score > 0 and regime.regime_score < config.min_regime_score:
                    decision = RegimeFilterDecision.REJECT
                    reasons.append(f"Long signal rejected in down trend with low regime score.")
                else:
                    decision = RegimeFilterDecision.REDUCE
                    reduction_factor = 0.5
                    reasons.append("Long signal reduced in risk-off/downtrend regime.")

            elif not is_long and regime.market_regime in (MarketRegime.TRENDING_UP, MarketRegime.RISK_ON):
                if config.min_regime_score > 0 and regime.regime_score > (100 - config.min_regime_score):
                    decision = RegimeFilterDecision.REJECT
                    reasons.append(f"Short signal rejected in strong uptrend with high regime score.")
                else:
                    decision = RegimeFilterDecision.REDUCE
                    reduction_factor = 0.5
                    reasons.append("Short signal reduced in risk-on/uptrend regime.")

        return decision, reduction_factor, reasons

    def adjust_score(self, signal: SignalCandidate, regime: RegimeClassification, config: RegimeConfig) -> tuple[float, float, list[str]]:
        reasons = []

        if config.mode in (RegimeScoreMode.METADATA_ONLY, RegimeScoreMode.FILTER_ONLY):
            return signal.score, signal.confidence, reasons

        adjusted_score = signal.score
        adjusted_conf = signal.confidence
        is_long = signal.direction == SignalDirection.LONG

        if is_long:
            if regime.regime_score > 60:
                adjusted_score += (regime.regime_score - 60) * 0.2
            elif regime.regime_score < 40:
                adjusted_score -= (40 - regime.regime_score) * 0.2
        else: # SHORT
            if regime.regime_score < 40:
                adjusted_score += (40 - regime.regime_score) * 0.2
            elif regime.regime_score > 60:
                adjusted_score -= (regime.regime_score - 60) * 0.2

        if regime.confidence < 50:
            adjusted_conf -= (50 - regime.confidence) * 0.2

        return max(0.0, min(100.0, adjusted_score)), max(0.0, min(100.0, adjusted_conf)), reasons

    def build_adjusted_signal(self, signal: SignalCandidate, adjusted_score: float, adjusted_confidence: float, regime: RegimeClassification, decision: RegimeFilterDecision) -> SignalCandidate:
        metadata = signal.metadata.copy() if signal.metadata else {}

        metadata.update({
            "regime_enabled": True,
            "market_regime": regime.market_regime.value,
            "trend_regime": regime.trend_regime.value,
            "volatility_regime": regime.volatility_regime.value,
            "liquidity_regime": regime.liquidity_regime.value,
            "momentum_regime": regime.momentum_regime.value,
            "regime_score": round(regime.regime_score, 2),
            "regime_confidence": round(regime.confidence, 2),
            "regime_filter_decision": decision.value,
            "regime_adjusted_score": round(adjusted_score, 2)
        })

        signal_dict = signal.model_dump()
        signal_dict["score"] = adjusted_score
        signal_dict["confidence"] = adjusted_confidence
        signal_dict["metadata"] = metadata

        return SignalCandidate(**signal_dict)

    def filter_signal(self, signal: SignalCandidate, regime: RegimeClassification, config: RegimeConfig | None = None) -> RegimeFilterResult:
        if config is None:
            config = RegimeConfig()

        decision, reduction_factor, dec_reasons = self._determine_decision(signal, regime, config)
        adjusted_score, adjusted_conf, adj_reasons = self.adjust_score(signal, regime, config)

        if decision == RegimeFilterDecision.REDUCE:
            adjusted_score *= reduction_factor

        adjusted_signal = self.build_adjusted_signal(signal, adjusted_score, adjusted_conf, regime, decision)

        return RegimeFilterResult(
            signal=signal,
            regime=regime,
            decision=decision,
            original_score=signal.score,
            adjusted_score=adjusted_score,
            original_confidence=signal.confidence,
            adjusted_confidence=adjusted_conf,
            reduction_factor=reduction_factor,
            reasons=dec_reasons + adj_reasons,
            adjusted_signal=adjusted_signal
        )
