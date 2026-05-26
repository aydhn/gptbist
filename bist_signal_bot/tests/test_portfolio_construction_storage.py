import pytest
import json
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.storage import PortfolioConstructionStore
from bist_signal_bot.portfolio_construction.models import RebalanceSimulation

def test_store_rebalance(tmp_path):
    settings = Settings()
    store = PortfolioConstructionStore(settings, base_dir=tmp_path)

    sim = RebalanceSimulation(
        rebalance_id="reb1",
        current_weights={"A": 0.5},
        target_weights={"A": 0.6},
        actions=[],
        estimated_turnover_pct=10.0
    )

    (tmp_path / 'recent').mkdir()
    store.append_rebalance(sim)
    loaded = store.load_latest_rebalance()
    assert loaded is not None
    assert loaded.rebalance_id == "reb1"
    assert loaded.estimated_turnover_pct == 10.0
