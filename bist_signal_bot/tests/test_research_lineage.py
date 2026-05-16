import pytest
from bist_signal_bot.research.lineage import ResearchLineageResolver
from bist_signal_bot.research.ledger import ResearchLedger
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import ResearchRun, ResearchRunType, ResearchRunStatus
from datetime import datetime

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def resolver(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    ledger = ResearchLedger(storage=store, settings=mock_settings)
    return ResearchLineageResolver(ledger=ledger)

def test_lineage_resolver(resolver):
    r1 = ResearchRun(run_id="r1", run_type=ResearchRunType.BACKTEST, status=ResearchRunStatus.SUCCESS, title="T1", started_at=datetime.utcnow())
    r2 = ResearchRun(run_id="r2", run_type=ResearchRunType.OPTIMIZATION, status=ResearchRunStatus.SUCCESS, title="T2", started_at=datetime.utcnow())

    resolver.ledger.append_run(r1)
    resolver.ledger.append_run(r2)

    res = resolver.link_runs("r1", "r2", "optimization_from_backtest")
    assert res["parent"] == "r1"

    children = resolver.find_children("r1")
    assert len(children) == 1
    assert children[0].run_id == "r2"

    parents = resolver.find_parents("r2")
    assert len(parents) == 1
    assert parents[0].run_id == "r1"

    summary = resolver.lineage_summary("r2")
    assert summary["parents_count"] == 1
    assert summary["children_count"] == 0
