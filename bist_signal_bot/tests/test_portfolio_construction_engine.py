import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.models import PortfolioConstructionRequest, PortfolioWeightingMethod
from bist_signal_bot.app.portfolio_construction_app import create_portfolio_construction_engine

def test_portfolio_construction_engine(tmp_path):

    class MockSettings:
        def __init__(self, d):
            self.PORTFOLIO_CONSTRUCTION_DIR_NAME = str(d)
            self.PORTFOLIO_CONSTRUCTION_SAVE_RESULTS = True
            self.PORTFOLIO_CONSTRUCTION_RESEARCH_ONLY = True
            self.PORTFOLIO_HIGH_CORRELATION_THRESHOLD = 0.75
            self.PORTFOLIO_RISK_BUDGET_ENABLED = True
            self.PORTFOLIO_MAX_SYMBOL_WEIGHT = 0.20
            self.PORTFOLIO_MAX_SECTOR_WEIGHT = 0.35
            self.PORTFOLIO_MAX_CORRELATION_CLUSTER_WEIGHT = 0.45
            self.PORTFOLIO_REBALANCE_MIN_DELTA_WEIGHT = 0.01
            self.PORTFOLIO_MIN_DIVERSIFICATION_SCORE = 50.0
            self.PORTFOLIO_MAX_TURNOVER_PCT = 50.0
            self.PORTFOLIO_MAX_COST_DRAG_BPS = 150.0

    settings = MockSettings(tmp_path)

    engine = create_portfolio_construction_engine(settings, base_dir=tmp_path)

    req = PortfolioConstructionRequest(
        request_id="req1",
        symbols=["ASELS", "GARAN"],
        strategy_names=["test"],
        weighting_method=PortfolioWeightingMethod.EQUAL_WEIGHT,
        max_positions=10,
        portfolio_notional=100000.0,
        current_weights={}
    )

    res = engine.construct(req)
    assert res.status.value in ["PASS", "WATCH", "FAIL"]
    assert len(res.positions) == 2
    assert res.positions[0].target_weight == 0.5
    assert res.positions[1].target_weight == 0.5

    # Store save_output
    assert "json" in res.output_files

    # Check save/load
    loaded = engine.store.load_latest_result()
    assert loaded is not None
    assert loaded.result_id == res.result_id
