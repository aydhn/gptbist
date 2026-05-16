import pytest
from datetime import datetime
from bist_signal_bot.research.query import ResearchQueryEngine
from bist_signal_bot.research.ledger import ResearchLedger
from bist_signal_bot.research.journal import SignalJournal
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import ResearchRun, ResearchRunType, ResearchRunStatus

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def engine(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    ledger = ResearchLedger(storage=store, settings=mock_settings)
    journal = SignalJournal(storage=store, settings=mock_settings)
    return ResearchQueryEngine(ledger=ledger, journal=journal)

def test_query_engine_find_failures(engine):
    r1 = ResearchRun(run_id="1", run_type=ResearchRunType.BACKTEST, status=ResearchRunStatus.SUCCESS, title="T1", started_at=datetime.utcnow())
    r2 = ResearchRun(run_id="2", run_type=ResearchRunType.BACKTEST, status=ResearchRunStatus.FAILED, title="T2", started_at=datetime.utcnow())
    engine.ledger.append_run(r1)
    engine.ledger.append_run(r2)

    failures = engine.find_recent_failures()
    assert len(failures) == 1
    assert failures[0].run_id == "2"
