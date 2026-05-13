import pandas as pd
from datetime import datetime
import logging

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.regime.models import (
    RegimeFeatureSet, RegimeClassification, RegimeConfig,
    TrendRegime, VolatilityRegime, LiquidityRegime, MomentumRegime, MarketRegime
)

class RegimeClassifier:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def _classify_trend(self, score: float) -> TrendRegime:
        if score >= 80: return TrendRegime.STRONG_UPTREND
        if score >= 60: return TrendRegime.UPTREND
        if score >= 40: return TrendRegime.RANGE
        if score >= 20: return TrendRegime.DOWNTREND
        return TrendRegime.STRONG_DOWNTREND

    def _classify_volatility(self, score: float) -> VolatilityRegime:
        if score >= 80: return VolatilityRegime.STRESS
        if score >= 60: return VolatilityRegime.HIGH
        if score >= 25: return VolatilityRegime.NORMAL
        return VolatilityRegime.LOW

    def _classify_liquidity(self, score: float) -> LiquidityRegime:
        if score >= 75: return LiquidityRegime.STRONG
        if score >= 45: return LiquidityRegime.NORMAL
        if score >= 20: return LiquidityRegime.WEAK
        return LiquidityRegime.ILLIQUID

    def _classify_momentum(self, score: float) -> MomentumRegime:
        if score >= 85: return MomentumRegime.EXTREME_POSITIVE
        if score >= 60: return MomentumRegime.POSITIVE
        if score >= 40: return MomentumRegime.NEUTRAL
        if score >= 15: return MomentumRegime.NEGATIVE
        return MomentumRegime.EXTREME_NEGATIVE

    def _determine_market_regime(self,
                                 trend: TrendRegime,
                                 vol: VolatilityRegime,
                                 liq: LiquidityRegime,
                                 mom: MomentumRegime,
                                 breakout_score: float) -> MarketRegime:
        if vol == VolatilityRegime.STRESS:
            return MarketRegime.HIGH_VOLATILITY_STRESS

        if liq == LiquidityRegime.ILLIQUID:
            return MarketRegime.LOW_LIQUIDITY

        if trend in (TrendRegime.STRONG_UPTREND, TrendRegime.UPTREND):
            if vol in (VolatilityRegime.LOW, VolatilityRegime.NORMAL) and liq in (LiquidityRegime.STRONG, LiquidityRegime.NORMAL):
                return MarketRegime.RISK_ON
            return MarketRegime.TRENDING_UP

        if trend in (TrendRegime.STRONG_DOWNTREND, TrendRegime.DOWNTREND):
            if vol in (VolatilityRegime.HIGH, VolatilityRegime.STRESS):
                return MarketRegime.RISK_OFF
            return MarketRegime.TRENDING_DOWN

        if trend == TrendRegime.RANGE:
            if breakout_score > 75 and vol != VolatilityRegime.STRESS:
                return MarketRegime.BREAKOUT_FRIENDLY
            if vol in (VolatilityRegime.LOW, VolatilityRegime.NORMAL):
                return MarketRegime.RANGE_BOUND
            return MarketRegime.MEAN_REVERSION_FRIENDLY

        return MarketRegime.MIXED

    def calculate_confidence(self, feature_set: RegimeFeatureSet) -> float:
        confidence = 100.0
        if not feature_set.timestamp:
            confidence -= 20.0
        exact_50_count = sum([
            feature_set.trend_score == 50.0,
            feature_set.volatility_score == 50.0,
            feature_set.liquidity_score == 50.0,
            feature_set.momentum_score == 50.0
        ])
        confidence -= (exact_50_count * 10.0)
        return max(0.0, min(100.0, confidence))

    def build_reasons(self, feature_set: RegimeFeatureSet, market_regime: MarketRegime) -> list[str]:
        reasons = []
        if market_regime == MarketRegime.RISK_ON:
            reasons.append("Strong uptrend with supportive normal/low volatility.")
        elif market_regime == MarketRegime.HIGH_VOLATILITY_STRESS:
            reasons.append("Volatility is at stress levels.")
        elif market_regime == MarketRegime.RANGE_BOUND:
            reasons.append("Trend is flat with contained volatility.")
        if feature_set.breakout_score > 75:
            reasons.append("High breakout pressure detected.")
        return reasons

    def classify(self, feature_set: RegimeFeatureSet, config: RegimeConfig | None = None) -> RegimeClassification:
        trend = self._classify_trend(feature_set.trend_score)
        vol = self._classify_volatility(feature_set.volatility_score)
        liq = self._classify_liquidity(feature_set.liquidity_score)
        mom = self._classify_momentum(feature_set.momentum_score)

        market_regime = self._determine_market_regime(trend, vol, liq, mom, feature_set.breakout_score)
        confidence = self.calculate_confidence(feature_set)
        reasons = self.build_reasons(feature_set, market_regime)

        return RegimeClassification(
            symbol=feature_set.symbol,
            timestamp=feature_set.timestamp,
            trend_regime=trend,
            volatility_regime=vol,
            liquidity_regime=liq,
            momentum_regime=mom,
            market_regime=market_regime,
            regime_score=feature_set.composite_regime_score,
            confidence=confidence,
            feature_set=feature_set,
            reasons=reasons
        )

    def classify_dataframe(self, data: pd.DataFrame, symbol: str, config: RegimeConfig | None = None) -> RegimeClassification:
        from bist_signal_bot.regime.features import RegimeFeatureBuilder
        builder = RegimeFeatureBuilder(self.settings)
        feature_set = builder.build_feature_set(data, symbol, config)
        return self.classify(feature_set, config)
