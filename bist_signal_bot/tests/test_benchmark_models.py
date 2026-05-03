import pytest
from bist_signal_bot.benchmarks.models import (
    BenchmarkSpec, BenchmarkCategory, BenchmarkRequest,
    BenchmarkSignal, BenchmarkPositionIntent
)

def test_benchmark_spec_validation():
    # Valid spec
    spec = BenchmarkSpec(
        name="test_bench",
        display_name="Test Bench",
        category=BenchmarkCategory.BUY_AND_HOLD,
        description="Test desc"
    )
    assert spec.name == "test_bench"

    # Invalid name
    with pytest.raises(ValueError, match="name must be lowercase snake_case"):
        BenchmarkSpec(name="Invalid-Name", display_name="Test", category=BenchmarkCategory.CUSTOM, description="Test desc")

    # Empty display name
    with pytest.raises(ValueError, match="display_name cannot be empty"):
        BenchmarkSpec(name="test", display_name="  ", category=BenchmarkCategory.CUSTOM, description="Test desc")

    # Invalid min rows
    with pytest.raises(ValueError, match="min_rows must be positive"):
        BenchmarkSpec(name="test", display_name="Test", category=BenchmarkCategory.CUSTOM, min_rows=0, description="Test desc")

def test_benchmark_request_normalization():
    req = BenchmarkRequest(
        benchmark_name="  TEST_bench  ",
        symbol=" asels ",
        symbols=[" garan", "thyao  "]
    )
    assert req.benchmark_name == "test_bench"
    assert req.symbol == "ASELS"
    assert req.symbols == ["GARAN", "THYAO"]

def test_benchmark_signal_validation():
    # Valid signal
    sig = BenchmarkSignal(
        symbol="ASELS",
        benchmark_name="test",
        intent=BenchmarkPositionIntent.LONG,
        score=50.0,
        weight=0.5
    )
    assert sig.score == 50.0

    # Invalid score
    with pytest.raises(ValueError, match="score must be between 0.0 and 100.0"):
        BenchmarkSignal(symbol="ASELS", benchmark_name="test", intent=BenchmarkPositionIntent.LONG, score=150.0)

    # Invalid weight
    with pytest.raises(ValueError, match="weight must be between 0.0 and 1.0"):
        BenchmarkSignal(symbol="ASELS", benchmark_name="test", intent=BenchmarkPositionIntent.LONG, score=50.0, weight=1.5)
