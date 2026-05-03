import pytest
import pandas as pd
from bist_signal_bot.benchmarks.strategies import (
    BuyAndHoldBenchmark, CashBenchmark, EqualWeightBenchmark,
    MovingAverageBenchmark, NaiveMomentumBenchmark,
    NaiveVolatilityFilterBenchmark, DeterministicRandomBaselineBenchmark
)
from bist_signal_bot.benchmarks.models import BenchmarkRequest, BenchmarkPositionIntent

@pytest.fixture
def mock_df():
    return pd.DataFrame({"close": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]})

def test_buy_and_hold(mock_df):
    bench = BuyAndHoldBenchmark()
    req = BenchmarkRequest(benchmark_name="buy_and_hold", symbol="ASELS")
    res = bench.run(mock_df, req)
    assert res.status.value == "SUCCESS"
    assert len(res.signals) == 1
    assert res.signals[0].intent == BenchmarkPositionIntent.LONG

def test_cash_benchmark():
    bench = CashBenchmark()
    req = BenchmarkRequest(benchmark_name="cash")
    res = bench.run(None, req)
    assert res.status.value == "SUCCESS"
    assert len(res.signals) == 1
    assert res.signals[0].intent == BenchmarkPositionIntent.FLAT
    assert res.signals[0].symbol == "CASH"

def test_equal_weight_benchmark(mock_df):
    bench = EqualWeightBenchmark()
    req = BenchmarkRequest(benchmark_name="equal_weight", symbols=["ASELS", "GARAN", "THYAO"])
    res = bench.run(mock_df, req)
    assert res.status.value == "SUCCESS"
    assert len(res.signals) == 3
    for s in res.signals:
        assert s.weight == pytest.approx(1.0 / 3)
        assert s.intent == BenchmarkPositionIntent.LONG

def test_moving_average_benchmark(mock_df):
    bench = MovingAverageBenchmark()
    req = BenchmarkRequest(benchmark_name="moving_average_benchmark", symbol="ASELS")
    res = bench.run(mock_df, req, params={"window": 3})
    assert res.status.value == "SUCCESS"
    # SMA3 of 130, 140, 150 is 140. close 150 > 140, so LONG
    assert res.signals[0].intent == BenchmarkPositionIntent.LONG

def test_naive_momentum(mock_df):
    bench = NaiveMomentumBenchmark()
    req = BenchmarkRequest(benchmark_name="naive_momentum", symbol="ASELS")
    res = bench.run(mock_df, req, params={"lookback": 2})
    assert res.status.value == "SUCCESS"
    # Return from index 3 (130) to 5 (150) is positive
    assert res.signals[0].intent == BenchmarkPositionIntent.LONG

def test_deterministic_random(mock_df):
    bench = DeterministicRandomBaselineBenchmark()
    req = BenchmarkRequest(benchmark_name="deterministic_random_baseline", symbol="ASELS")
    res1 = bench.run(mock_df, req, params={"seed": 42})
    res2 = bench.run(mock_df, req, params={"seed": 42})
    assert res1.signals[0].intent == res2.signals[0].intent

    # Different seed could be different, but deterministic.
    # At least check the mechanics
    assert res1.status.value == "SUCCESS"
