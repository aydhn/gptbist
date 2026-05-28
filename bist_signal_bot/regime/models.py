from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.core.exceptions import RegimeValidationError

class TrendRegime(Enum):
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    RANGE = "RANGE"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"
    UNKNOWN = "UNKNOWN"

class VolatilityRegime(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    STRESS = "STRESS"
    UNKNOWN = "UNKNOWN"

class LiquidityRegime(Enum):
    STRONG = "STRONG"
    NORMAL = "NORMAL"
    WEAK = "WEAK"
    ILLIQUID = "ILLIQUID"
    UNKNOWN = "UNKNOWN"

class MomentumRegime(Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    EXTREME_POSITIVE = "EXTREME_POSITIVE"
    EXTREME_NEGATIVE = "EXTREME_NEGATIVE"
    UNKNOWN = "UNKNOWN"

class MarketRegime(Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGE_BOUND = "RANGE_BOUND"
    BREAKOUT_FRIENDLY = "BREAKOUT_FRIENDLY"
    MEAN_REVERSION_FRIENDLY = "MEAN_REVERSION_FRIENDLY"
    HIGH_VOLATILITY_STRESS = "HIGH_VOLATILITY_STRESS"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"

class RegimeFilterDecision(Enum):
    PASS = "PASS"
    REDUCE = "REDUCE"
    REJECT = "REJECT"
    WATCH_ONLY = "WATCH_ONLY"
    SKIP = "SKIP"
    ERROR = "ERROR"

class RegimeScoreMode(Enum):
    METADATA_ONLY = "METADATA_ONLY"
    FILTER_ONLY = "FILTER_ONLY"
    SCORE_ADJUST = "SCORE_ADJUST"
    FILTER_AND_SCORE = "FILTER_AND_SCORE"

class RegimeConfig(BaseModel):
    trend_window: int = Field(default=50, gt=0)
    volatility_window: int = Field(default=20, gt=0)
    momentum_window: int = Field(default=20, gt=0)
    liquidity_window: int = Field(default=20, gt=0)
    correlation_window: int = Field(default=60, gt=0)
    use_mtf: bool = False
    use_benchmark_relative: bool = False
    mode: RegimeScoreMode = RegimeScoreMode.FILTER_AND_SCORE
    min_regime_score: float = Field(default=40.0, ge=0.0, le=100.0)
    reject_stress_regime: bool = False
    reduce_in_stress: bool = True
    stress_reduction_factor: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RegimeFeatureSet(BaseModel):
    symbol: str
    timestamp: datetime | None = None
    trend_score: float = Field(ge=0.0, le=100.0)
    volatility_score: float = Field(ge=0.0, le=100.0)
    liquidity_score: float = Field(ge=0.0, le=100.0)
    momentum_score: float = Field(ge=0.0, le=100.0)
    range_score: float = Field(ge=0.0, le=100.0)
    breakout_score: float = Field(ge=0.0, le=100.0)
    correlation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    benchmark_relative_score: float | None = Field(default=None, ge=0.0, le=100.0)
    composite_regime_score: float = Field(ge=0.0, le=100.0)
    features: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        self.symbol = self.symbol.upper()

class RegimeClassification(BaseModel):
    symbol: str
    timestamp: datetime | None = None
    trend_regime: TrendRegime
    volatility_regime: VolatilityRegime
    liquidity_regime: LiquidityRegime
    momentum_regime: MomentumRegime
    market_regime: MarketRegime
    regime_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    feature_set: RegimeFeatureSet
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    disclaimer: str = "Market regime research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
    breadth_regime_label: str | None = None
    breadth_score: float | None = None
    participation_score: float | None = None
    divergence_warning: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "market_regime": self.market_regime.value,
            "trend_regime": self.trend_regime.value,
            "volatility_regime": self.volatility_regime.value,
            "liquidity_regime": self.liquidity_regime.value,
            "momentum_regime": self.momentum_regime.value,
            "regime_score": round(self.regime_score, 2),
            "confidence": round(self.confidence, 2)
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "market_regime": self.market_regime.value,
            "trend_regime": self.trend_regime.value,
            "volatility_regime": self.volatility_regime.value,
            "liquidity_regime": self.liquidity_regime.value,
            "momentum_regime": self.momentum_regime.value,
            "regime_score": round(self.regime_score, 2),
            "confidence": round(self.confidence, 2),
            "reasons": self.reasons,
            "warnings": self.warnings,
            "disclaimer": self.disclaimer
        }

class RegimeFilterResult(BaseModel):
    signal: SignalCandidate
    regime: RegimeClassification
    decision: RegimeFilterDecision
    original_score: float
    adjusted_score: float
    original_confidence: float
    adjusted_confidence: float
    reduction_factor: float
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    adjusted_signal: SignalCandidate
    metadata: dict[str, Any] = Field(default_factory=dict)

class RegimeBatchResult(BaseModel):
    classifications: list[RegimeClassification] = Field(default_factory=list)
    filter_results: list[RegimeFilterResult] = Field(default_factory=list)
    requested_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.now)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Market regime research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "classifications": len(self.classifications),
            "filter_results": len(self.filter_results)
        }

class UniverseRegimeReport(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    classifications: list[RegimeClassification] = Field(default_factory=list)
    market_regime_counts: dict[str, int] = Field(default_factory=dict)
    trend_regime_counts: dict[str, int] = Field(default_factory=dict)
    volatility_regime_counts: dict[str, int] = Field(default_factory=dict)
    risk_on_pct: float = 0.0
    risk_off_pct: float = 0.0
    stress_pct: float = 0.0
    average_regime_score: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.now)
    elapsed_seconds: float = 0.0
    issues: list[str] = Field(default_factory=list)
    disclaimer: str = "Market regime research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol_count": len(self.symbols),
            "risk_on_pct": round(self.risk_on_pct, 2),
            "risk_off_pct": round(self.risk_off_pct, 2),
            "stress_pct": round(self.stress_pct, 2),
            "average_regime_score": round(self.average_regime_score, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2)
        }
