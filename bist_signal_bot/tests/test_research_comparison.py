import pytest
from bist_signal_bot.research.comparison import ResearchComparator
from bist_signal_bot.research.ledger import ResearchLedger
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import ResearchComparisonItem, ResearchRunType

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def comparator(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    ledger = ResearchLedger(storage=store, settings=mock_settings)
    return ResearchComparator(ledger=ledger, settings=mock_settings)

def test_comparator_rank_items(comparator):
    items = [
        ResearchComparisonItem(run_id="r1", run_type=ResearchRunType.BACKTEST, label="L1", metrics={"sharpe": 1.0}),
        ResearchComparisonItem(run_id="r2", run_type=ResearchRunType.BACKTEST, label="L2", metrics={"sharpe": 1.5}),
        ResearchComparisonItem(run_id="r3", run_type=ResearchRunType.BACKTEST, label="L3", metrics={}) # Missing metric
    ]
    ranked = comparator.rank_items(items, metric="sharpe")
    assert ranked[0].run_id == "r2"
    assert ranked[1].run_id == "r1"
    assert ranked[2].run_id == "r3"
    assert ranked[0].rank == 1

    # Test inverse metric
    items2 = [
        ResearchComparisonItem(run_id="r1", run_type=ResearchRunType.BACKTEST, label="L1", metrics={"max_drawdown_pct": 20.0}),
        ResearchComparisonItem(run_id="r2", run_type=ResearchRunType.BACKTEST, label="L2", metrics={"max_drawdown_pct": 10.0}),
        ResearchComparisonItem(run_id="r3", run_type=ResearchRunType.BACKTEST, label="L3", metrics={}) # Missing metric
    ]
    ranked2 = comparator.rank_items(items2, metric="max_drawdown_pct")
    assert ranked2[0].run_id == "r2"
    assert ranked2[1].run_id == "r1"
    assert ranked2[2].run_id == "r3"
