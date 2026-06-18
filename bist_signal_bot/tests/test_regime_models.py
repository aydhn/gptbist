import pytest
from bist_signal_bot.regime.models import UniverseRegimeReport

def test_universe_regime_report_summary():
    report = UniverseRegimeReport(
        symbols=["AAPL", "MSFT", "GOOG"],
        risk_on_pct=45.678,
        risk_off_pct=54.321,
        stress_pct=12.345,
        average_regime_score=67.891,
        elapsed_seconds=1.234
    )

    summary = report.summary()

    assert summary["symbol_count"] == 3
    assert summary["risk_on_pct"] == 45.68
    assert summary["risk_off_pct"] == 54.32
    assert summary["stress_pct"] == 12.35
    assert summary["average_regime_score"] == 67.89
    assert summary["elapsed_seconds"] == 1.23

def test_universe_regime_report_summary_empty():
    report = UniverseRegimeReport()

    summary = report.summary()

    assert summary["symbol_count"] == 0
    assert summary["risk_on_pct"] == 0.0
    assert summary["risk_off_pct"] == 0.0
    assert summary["stress_pct"] == 0.0
    assert summary["average_regime_score"] == 0.0
    assert summary["elapsed_seconds"] == 0.0

from datetime import datetime
from bist_signal_bot.regime.models import (
    RegimeClassification,
    TrendRegime,
    VolatilityRegime,
    LiquidityRegime,
    MomentumRegime,
    MarketRegime,
    RegimeFeatureSet
)

def test_regime_classification_summary():
    feature_set = RegimeFeatureSet(
        symbol="AAPL",
        trend_score=80.0,
        volatility_score=20.0,
        liquidity_score=90.0,
        momentum_score=70.0,
        range_score=30.0,
        breakout_score=60.0,
        composite_regime_score=75.0
    )

    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    classification = RegimeClassification(
        symbol="AAPL",
        timestamp=timestamp,
        trend_regime=TrendRegime.UPTREND,
        volatility_regime=VolatilityRegime.LOW,
        liquidity_regime=LiquidityRegime.STRONG,
        momentum_regime=MomentumRegime.POSITIVE,
        market_regime=MarketRegime.RISK_ON,
        regime_score=85.123,
        confidence=90.456,
        feature_set=feature_set
    )

    summary = classification.summary()

    assert summary["symbol"] == "AAPL"
    assert summary["timestamp"] == "2023-01-01T12:00:00"
    assert summary["market_regime"] == "RISK_ON"
    assert summary["trend_regime"] == "UPTREND"
    assert summary["volatility_regime"] == "LOW"
    assert summary["liquidity_regime"] == "STRONG"
    assert summary["momentum_regime"] == "POSITIVE"
    assert summary["regime_score"] == 85.12
    assert summary["confidence"] == 90.46

def test_regime_classification_safe_public_dict():
    feature_set = RegimeFeatureSet(
        symbol="AAPL",
        trend_score=80.0,
        volatility_score=20.0,
        liquidity_score=90.0,
        momentum_score=70.0,
        range_score=30.0,
        breakout_score=60.0,
        composite_regime_score=75.0
    )

    classification = RegimeClassification(
        symbol="AAPL",
        trend_regime=TrendRegime.UPTREND,
        volatility_regime=VolatilityRegime.LOW,
        liquidity_regime=LiquidityRegime.STRONG,
        momentum_regime=MomentumRegime.POSITIVE,
        market_regime=MarketRegime.RISK_ON,
        regime_score=85.123,
        confidence=90.456,
        feature_set=feature_set,
        reasons=["reason1", "reason2"],
        warnings=["warning1"]
    )

    safe_dict = classification.safe_public_dict()

    assert safe_dict["symbol"] == "AAPL"
    assert safe_dict["market_regime"] == "RISK_ON"
    assert safe_dict["trend_regime"] == "UPTREND"
    assert safe_dict["volatility_regime"] == "LOW"
    assert safe_dict["liquidity_regime"] == "STRONG"
    assert safe_dict["momentum_regime"] == "POSITIVE"
    assert safe_dict["regime_score"] == 85.12
    assert safe_dict["confidence"] == 90.46
    assert safe_dict["reasons"] == ["reason1", "reason2"]
    assert safe_dict["warnings"] == ["warning1"]
    assert safe_dict["disclaimer"] == "Market regime research output only. Not investment advice. No order was sent."

from bist_signal_bot.regime.models import RegimeBatchResult

def test_regime_batch_result_summary():
    result = RegimeBatchResult(
        requested_count=10,
        success_count=8,
        failed_count=2,
        elapsed_seconds=5.678,
        classifications=[{"symbol": "A", "trend_regime": "UPTREND", "volatility_regime": "LOW", "liquidity_regime": "STRONG", "momentum_regime": "POSITIVE", "market_regime": "RISK_ON", "regime_score": 50, "confidence": 50, "feature_set": {"symbol": "A", "trend_score": 50, "volatility_score": 50, "liquidity_score": 50, "momentum_score": 50, "range_score": 50, "breakout_score": 50, "composite_regime_score": 50}}, {"symbol": "A", "trend_regime": "UPTREND", "volatility_regime": "LOW", "liquidity_regime": "STRONG", "momentum_regime": "POSITIVE", "market_regime": "RISK_ON", "regime_score": 50, "confidence": 50, "feature_set": {"symbol": "A", "trend_score": 50, "volatility_score": 50, "liquidity_score": 50, "momentum_score": 50, "range_score": 50, "breakout_score": 50, "composite_regime_score": 50}}, {"symbol": "A", "trend_regime": "UPTREND", "volatility_regime": "LOW", "liquidity_regime": "STRONG", "momentum_regime": "POSITIVE", "market_regime": "RISK_ON", "regime_score": 50, "confidence": 50, "feature_set": {"symbol": "A", "trend_score": 50, "volatility_score": 50, "liquidity_score": 50, "momentum_score": 50, "range_score": 50, "breakout_score": 50, "composite_regime_score": 50}}], # 3 dummy items to test len
        filter_results=[{"signal": {"symbol": "A", "direction": "LONG", "score": 50, "confidence": 50, "strategy_name": "S1"}, "regime": {"symbol": "A", "trend_regime": "UPTREND", "volatility_regime": "LOW", "liquidity_regime": "STRONG", "momentum_regime": "POSITIVE", "market_regime": "RISK_ON", "regime_score": 50, "confidence": 50, "feature_set": {"symbol": "A", "trend_score": 50, "volatility_score": 50, "liquidity_score": 50, "momentum_score": 50, "range_score": 50, "breakout_score": 50, "composite_regime_score": 50}}, "decision": "PASS", "original_score": 50, "adjusted_score": 50, "original_confidence": 50, "adjusted_confidence": 50, "reduction_factor": 1, "adjusted_signal": {"symbol": "A", "direction": "LONG", "score": 50, "confidence": 50, "strategy_name": "S1"}}, {"signal": {"symbol": "A", "direction": "LONG", "score": 50, "confidence": 50, "strategy_name": "S1"}, "regime": {"symbol": "A", "trend_regime": "UPTREND", "volatility_regime": "LOW", "liquidity_regime": "STRONG", "momentum_regime": "POSITIVE", "market_regime": "RISK_ON", "regime_score": 50, "confidence": 50, "feature_set": {"symbol": "A", "trend_score": 50, "volatility_score": 50, "liquidity_score": 50, "momentum_score": 50, "range_score": 50, "breakout_score": 50, "composite_regime_score": 50}}, "decision": "PASS", "original_score": 50, "adjusted_score": 50, "original_confidence": 50, "adjusted_confidence": 50, "reduction_factor": 1, "adjusted_signal": {"symbol": "A", "direction": "LONG", "score": 50, "confidence": 50, "strategy_name": "S1"}}] # 2 dummy items to test len
    )

    summary = result.summary()

    assert summary["requested_count"] == 10
    assert summary["success_count"] == 8
    assert summary["failed_count"] == 2
    assert summary["elapsed_seconds"] == 5.68
    assert summary["classifications"] == 3
    assert summary["filter_results"] == 2
