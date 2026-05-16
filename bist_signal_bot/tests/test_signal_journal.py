import pytest
from bist_signal_bot.research.journal import SignalJournal
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import SignalJournalEntry, ResearchSignalOutcome
from datetime import datetime

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def journal(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    return SignalJournal(storage=store, settings=mock_settings)

class MockSignal:
    def __init__(self, s, st, d, sc):
        self.symbol = s
        self.strategy_name = st
        self.direction = d
        self.score = sc

def test_journal_from_candidate(journal):
    sig = MockSignal("ASELS", "s1", "LONG", 80.0)
    entry = journal.from_signal_candidate(sig)
    assert entry.symbol == "ASELS"
    assert entry.direction == "LONG"

    entries = journal.load_entries()
    assert len(entries) == 1

def test_journal_outcome_update(journal):
    sig = MockSignal("THYAO", "s2", "SHORT", 90.0)
    entry = journal.from_signal_candidate(sig)

    with pytest.raises(Exception):
        journal.settings.RESEARCH_JOURNAL_REQUIRE_CONFIRM_FOR_OUTCOME_UPDATE = True
        journal.update_outcome(entry.journal_id, ResearchSignalOutcome.POSITIVE)

    updated = journal.update_outcome(entry.journal_id, ResearchSignalOutcome.POSITIVE, outcome_return_pct=2.5, horizon_bars=5, confirm=True)
    assert updated.outcome == ResearchSignalOutcome.POSITIVE
    assert updated.outcome_return_pct == 2.5

    entries = journal.load_entries()
    # It's an append only store
    assert len(entries) == 2
