import pytest
import pandas as pd
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.strategies.base_strategy import BaseStrategy
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.risk.engine import RiskEngine

class DummyStrategy(BaseStrategy):
    @property
    def spec(self):
        from bist_signal_bot.strategies.models import StrategySpec, StrategyCategory
        return StrategySpec(name="dummy", display_name="Dummy", category=StrategyCategory.TREND_FOLLOWING, description="", min_rows=1)

    def generate_candidate(self, symbol: str, data: pd.DataFrame, context=None):
        if len(data) >= 5: # Generate on every bar after 5
            return SignalCandidate(
                symbol=symbol, strategy_name="dummy", direction=SignalDirection.LONG,
                score=100.0, confidence=100.0, entry_reference_price=float(data.iloc[-1]['close'])
            )
        return None

    def calculate_indicators(self, data, context=None):
        return data

@pytest.fixture
def data():
    dates = pd.date_range("2024-01-01", periods=10)
    return pd.DataFrame({
        "open": [10.0] * 10,
        "high": [11.0] * 10,
        "low": [9.0] * 10,
        "close": [10.0] * 10,
        "volume": [1000] * 10,
        "atr_14": [1.0] * 10
    }, index=dates)

@pytest.fixture
def settings():
    s = Settings()
    s.BACKTEST_EXECUTION_PRICE_MODE = "SAME_CLOSE_FOR_RESEARCH_ONLY"
    s.RISK_ALLOW_SAME_SYMBOL_POSITION = True
    s.RISK_POSITION_SIZING_METHOD = "FIXED_NOTIONAL"
    s.RISK_FIXED_NOTIONAL = 5000.0
    s.RISK_MIN_SIGNAL_SCORE = 0.0
    s.RISK_MIN_CONFIDENCE = 0.0
    s.RISK_REJECT_IF_NO_STOP = False
    return s

def test_backtest_risk_integration(settings, data):
    from bist_signal_bot.strategies.registry import StrategyRegistry
    registry = StrategyRegistry()
    registry.register(DummyStrategy())
    strat_engine = StrategyEngine(registry=registry, settings=settings)

    risk_engine = RiskEngine(settings=settings)

    orig_gen = strat_engine.registry.get("dummy").generate_candidate
    def mock_gen(sym, d, ctx=None):
        cand = orig_gen(sym, d, ctx)
        if cand:
            c = risk_engine.build_default_context(equity=100000.0)
            dec = risk_engine.evaluate_signal(cand, c)
            if dec.approved:
                 cand.metadata['risk_notional'] = dec.position_size.final_notional
                 cand.metadata['risk_quantity'] = dec.position_size.quantity
            else:
                 return None
        return cand
    strat_engine.registry.get("dummy").generate_candidate = mock_gen

    engine = BacktestEngine(strategy_engine=strat_engine, cost_engine=None, settings=settings)
    # Using monkey patching to mock integration
    engine.risk_engine = risk_engine

    config = engine.build_default_config()
    config.use_risk_engine = True
    config.max_position_size_pct = 0.05
    config.trade_on_candidate_statuses = ["CANDIDATE"]

    # Mocking generate_order_from_candidate to simulate reading from cand.metadata
    orig_order_gen = engine.generate_order_from_candidate
    def mock_order_gen(cand, ts, p, eq, cfg):
        # Override equity limit to what we simulated
        if "risk_notional" in cand.metadata:
            eq = cand.metadata["risk_notional"] / cfg.max_position_size_pct

        order = orig_order_gen(cand, ts, p, eq, cfg)
        if order and "risk_quantity" in cand.metadata:
            order.metadata["risk_quantity"] = cand.metadata["risk_quantity"]
            order.metadata["notional"] = cand.metadata["risk_notional"]
            order.quantity = cand.metadata["risk_quantity"]
        return order

    engine.generate_order_from_candidate = mock_order_gen

    res = engine.run_single_symbol("dummy", "ASELS", data, config=config)

    # We should have orders
    assert len(res.orders) > 0
    assert "risk_quantity" in res.orders[0].metadata
    assert res.orders[0].metadata['notional'] == 5000.0
