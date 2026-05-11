import pandas as pd
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Any

from bist_signal_bot.signals.models import SignalCandidate

class MLInferenceMode(str, Enum):
    SCORE_ONLY = "SCORE_ONLY"
    FILTER_ONLY = "FILTER_ONLY"
    SCORE_AND_FILTER = "SCORE_AND_FILTER"
    DISABLED = "DISABLED"

class MLFilterDecision(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"
    WATCH_ONLY = "WATCH_ONLY"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

class MLScoreBlendMode(str, Enum):
    REPLACE = "REPLACE"
    WEIGHTED_AVERAGE = "WEIGHTED_AVERAGE"
    ADDITIVE_BONUS = "ADDITIVE_BONUS"
    PENALTY_ONLY = "PENALTY_ONLY"
    METADATA_ONLY = "METADATA_ONLY"

class MLPredictionDirection(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"

class MLFeatureAlignmentStatus(str, Enum):
    ALIGNED = "ALIGNED"
    MISSING_FEATURES = "MISSING_FEATURES"
    EXTRA_FEATURES = "EXTRA_FEATURES"
    ORDER_MISMATCH_FIXED = "ORDER_MISMATCH_FIXED"
    FAILED = "FAILED"

class MLInferenceConfig(BaseModel):
    enabled: bool = Field(default=True)
    model_id: str | None = Field(default=None)
    model_path: str | None = Field(default=None)
    mode: MLInferenceMode = Field(default=MLInferenceMode.SCORE_AND_FILTER)
    blend_mode: MLScoreBlendMode = Field(default=MLScoreBlendMode.WEIGHTED_AVERAGE)
    ml_score_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    strategy_score_weight: float = Field(default=0.65, ge=0.0, le=1.0)
    min_probability_positive: float = Field(default=0.55, ge=0.0, le=1.0)
    max_probability_negative: float = Field(default=0.60, ge=0.0, le=1.0)
    min_prediction_score: float = Field(default=50.0, ge=0.0, le=100.0)
    reject_on_missing_features: bool = Field(default=True)
    allow_extra_features: bool = Field(default=True)
    latest_only: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_model_id_path(self):
        if self.enabled and not self.model_id and not self.model_path:
            raise ValueError("model_id or model_path is required when inference is enabled")
        return self

class MLFeatureAlignmentResult(BaseModel):
    status: MLFeatureAlignmentStatus
    required_features: list[str] = Field(default_factory=list)
    available_features: list[str] = Field(default_factory=list)
    missing_features: list[str] = Field(default_factory=list)
    extra_features: list[str] = Field(default_factory=list)
    aligned_data: pd.DataFrame | None = Field(default=None)
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "missing_count": len(self.missing_features),
            "extra_count": len(self.extra_features),
            "issues": self.issues
        }

class MLInferenceInput(BaseModel):
    symbol: str
    data: pd.DataFrame
    signal: SignalCandidate | None = Field(default=None)
    config: MLInferenceConfig
    timeframe: str = Field(default="1d")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class MLInferenceResult(BaseModel):
    symbol: str
    model_id: str
    prediction_direction: MLPredictionDirection
    prediction_value: float | int | str | None = Field(default=None)
    prediction_score: float = Field(default=0.0)
    probability_positive: float | None = Field(default=None)
    probability_negative: float | None = Field(default=None)
    probability_neutral: float | None = Field(default=None)
    filter_decision: MLFilterDecision
    original_signal_score: float | None = Field(default=None)
    adjusted_signal_score: float | None = Field(default=None)
    original_confidence: float | None = Field(default=None)
    adjusted_confidence: float | None = Field(default=None)
    alignment: MLFeatureAlignmentResult
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime
    elapsed_seconds: float
    disclaimer: str = Field(default="ML inference research output only. Prediction is not investment advice. No order was sent.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "model_id": self.model_id,
            "prediction_direction": self.prediction_direction.value,
            "prediction_score": self.prediction_score,
            "probability_positive": self.probability_positive,
            "filter_decision": self.filter_decision.value,
            "adjusted_signal_score": self.adjusted_signal_score,
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.summary()
        d["disclaimer"] = self.disclaimer
        return d

class MLSignalFilterResult(BaseModel):
    signal: SignalCandidate
    inference_result: MLInferenceResult
    passed: bool
    adjusted_signal: SignalCandidate
    reject_reason: str | None = Field(default=None)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class MLInferenceBatchResult(BaseModel):
    results: list[MLInferenceResult] = Field(default_factory=list)
    signal_filter_results: list[MLSignalFilterResult] = Field(default_factory=list)
    requested_count: int = Field(default=0)
    passed_count: int = Field(default=0)
    rejected_count: int = Field(default=0)
    error_count: int = Field(default=0)
    generated_at: datetime
    elapsed_seconds: float
    disclaimer: str = Field(default="ML inference research output only. Prediction is not investment advice. No order was sent.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def summary(self) -> dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "passed_count": self.passed_count,
            "rejected_count": self.rejected_count,
            "error_count": self.error_count,
            "elapsed_seconds": self.elapsed_seconds,
            "disclaimer": self.disclaimer
        }
