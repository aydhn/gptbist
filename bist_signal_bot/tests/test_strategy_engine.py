import pytest
import pandas as pd
from typing import Any

from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.strategies.registry import StrategyRegistry
from bist_signal_bot.strategies.base_strategy import BaseStrategy
from bist_signal_bot.strategies.models import StrategySpec
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

class MockLongStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(name="mock_long", display_name="Mock Long")

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        return self.build_signal_candidate(context, SignalDirection.LONG, score=80.0)

class MockWatchStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(name="mock_watch", display_name="Mock Watch")

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        return self.build_signal_candidate(context, SignalDirection.WATCH, score=40.0)

class MockErrorStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(name="mock_error", display_name="Mock Error")

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        raise ValueError("Simulated failure")

def setup_engine():
    registry = StrategyRegistry()
    registry.register(MockLongStrategy())
    registry.register(MockWatchStrategy())
    registry.register(MockErrorStrategy())
    return StrategyEngine(registry=registry)

def test_engine_uses_builtin_registry_by_default():
    engine = StrategyEngine()

    assert engine.registry.exists("moving_average_trend")

def test_engine_run_on_data_success():
    engine = setup_engine()
    df = pd.DataFrame({"close": [1, 2, 3]})

    res = engine.run_strategy_on_data("mock_long", "ASELS", df)

    assert res.status == "success"
    assert res.candidate is not None
    assert res.candidate.direction == SignalDirection.LONG
    assert res.candidate.score == 80.0

def test_engine_run_on_data_error():
    engine = setup_engine()
    df = pd.DataFrame({"close": [1, 2, 3]})

    res = engine.run_strategy_on_data("mock_error", "ASELS", df)

    assert res.status == "error"
    assert "Simulated failure" in res.issues[0].message

def test_engine_parse_params():
    engine = setup_engine()
    params = engine.parse_params(["fast=20", "slow=50", "thresh=0.05", "flag=true"])

    assert params["fast"] == 20
    assert params["slow"] == 50
    assert params["thresh"] == 0.05
    assert params["flag"] is True

def test_batch_summary_counts():
    engine = setup_engine()

    class DummyDataService:
        def fetch_one(self, symbol, timeframe):
            return pd.DataFrame({"close": [100]})

    engine.data_service = DummyDataService()

    # Batch run
    batch = engine.run_strategy_batch("mock_long", ["ASELS", "GARAN", "THYAO"])
    assert batch.symbol_count == 3
    assert batch.success_count == 3
    assert batch.long_count() == 3
    assert batch.watch_count() == 0

    batch2 = engine.run_strategy_batch("mock_watch", ["ASELS", "GARAN"])
    assert batch2.watch_count() == 2
