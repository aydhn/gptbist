import pytest
import pandas as pd
from bist_signal_bot.benchmarks.engine import BenchmarkEngine, benchmark_signal_to_candidate
from bist_signal_bot.benchmarks.models import BenchmarkSignal, BenchmarkPositionIntent
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def engine():
    settings = Settings()
    return BenchmarkEngine(settings=settings)

def test_engine_run_on_data(engine):
    df = pd.DataFrame({"close": [100.0, 110.0, 120.0]})
    res = engine.run_on_data("buy_and_hold", "ASELS", df)
    assert res.status.value == "SUCCESS"
    assert res.signals[0].intent.value == "LONG"


def test_engine_batch(engine):
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    engine.data_service = MockMarketDataProvider()
    # Mock symbols and simple benchmark

    res = engine.run_batch("cash", ["ASELS", "GARAN"])
    assert res.success_count == 2
    assert len(res.results) == 2

def test_engine_parse_params(engine):
    params = engine.parse_params(["window=50", "flag=true", "max=0.5"])
    assert params["window"] == 50
    assert params["flag"] is True
    assert params["max"] == 0.5

def test_benchmark_signal_to_candidate():
    sig = BenchmarkSignal(
        symbol="ASELS",
        benchmark_name="cash",
        intent=BenchmarkPositionIntent.FLAT,
        score=50.0,
        reference_price=10.0
    )
    cand = benchmark_signal_to_candidate(sig)
    assert cand.direction.value == "FLAT"
    assert cand.strategy_name == "cash"
    assert cand.score == 50.0
