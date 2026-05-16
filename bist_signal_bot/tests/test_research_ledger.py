import pytest
from pathlib import Path
from bist_signal_bot.research.ledger import ResearchLedger
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import ResearchRun, ResearchRunType, ResearchRunStatus, ResearchTag, ResearchQuery
from datetime import datetime

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    s.RESEARCH_DIR_NAME = "test_research"
    return s

@pytest.fixture
def ledger(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    return ResearchLedger(storage=store, settings=mock_settings)

def test_ledger_append_and_load(ledger):
    run = ResearchRun(
        run_id="run1",
        run_type=ResearchRunType.BACKTEST,
        status=ResearchRunStatus.SUCCESS,
        title="R1",
        started_at=datetime.utcnow(),
        symbols=["ASELS"]
    )
    entry = ledger.append_run(run)
    assert entry.entry_id.startswith("rle_")

    entries = ledger.load_entries()
    assert len(entries) == 1
    assert entries[0].run.run_id == "run1"

def test_ledger_get_run(ledger):
    run = ResearchRun(
        run_id="run2",
        run_type=ResearchRunType.SIGNAL_SCAN,
        status=ResearchRunStatus.SUCCESS,
        title="R2",
        started_at=datetime.utcnow()
    )
    ledger.append_run(run)
    loaded = ledger.get_run("run2")
    assert loaded is not None
    assert loaded.title == "R2"
    assert ledger.get_run("non_existent") is None

def test_ledger_tag_run(ledger):
    run = ResearchRun(
        run_id="run3",
        run_type=ResearchRunType.MANUAL_NOTE,
        status=ResearchRunStatus.SUCCESS,
        title="R3",
        started_at=datetime.utcnow()
    )
    ledger.append_run(run)

    # Needs confirm
    with pytest.raises(Exception):
        ledger.settings.RESEARCH_REQUIRE_CONFIRM_FOR_TAG_EDIT = True
        ledger.tag_run("run3", [ResearchTag(tag="newtag")])

    updated = ledger.tag_run("run3", [ResearchTag(tag="newtag")], confirm=True)
    assert any(t.tag == "newtag" for t in updated.tags)

    entries = ledger.load_entries()
    # Should have two entries representing the state before and after
    assert len(entries) == 2

def test_ledger_query(ledger):
    run = ResearchRun(
        run_id="run4",
        run_type=ResearchRunType.BACKTEST,
        status=ResearchRunStatus.SUCCESS,
        title="R4",
        started_at=datetime.utcnow(),
        symbols=["THYAO"]
    )
    ledger.append_run(run)

    q1 = ResearchQuery(symbols=["THYAO"])
    assert len(ledger.load_entries(query=q1)) == 1

    q2 = ResearchQuery(symbols=["GARAN"])
    assert len(ledger.load_entries(query=q2)) == 0
