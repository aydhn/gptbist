import pytest
from bist_signal_bot.research.attribution import ResearchAttributionEngine
from bist_signal_bot.research.journal import SignalJournal
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research.models import SignalJournalEntry, AttributionGroupBy, ResearchSignalOutcome

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def engine(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    journal = SignalJournal(storage=store, settings=mock_settings)
    return ResearchAttributionEngine(journal=journal, settings=mock_settings)

def test_attribution_group_by_symbol(engine):
    entries = [
        SignalJournalEntry(journal_id="1", symbol="ASELS", strategy_name="S1", outcome=ResearchSignalOutcome.POSITIVE, outcome_return_pct=2.0),
        SignalJournalEntry(journal_id="2", symbol="ASELS", strategy_name="S1", outcome=ResearchSignalOutcome.NEGATIVE, outcome_return_pct=-1.0),
        SignalJournalEntry(journal_id="3", symbol="THYAO", strategy_name="S1", outcome=ResearchSignalOutcome.POSITIVE, outcome_return_pct=3.0)
    ]

    report = engine.build_attribution_from_journal(entries, AttributionGroupBy.SYMBOL)
    assert report.group_by == AttributionGroupBy.SYMBOL
    assert len(report.buckets) == 2

    asels_b = next(b for b in report.buckets if b.group_key == "ASELS")
    assert asels_b.count == 2
    assert asels_b.win_rate == 50.0

    thyao_b = next(b for b in report.buckets if b.group_key == "THYAO")
    assert thyao_b.win_rate == 100.0

def test_attribution_ml_bucket(engine):
    entries = [
        SignalJournalEntry(journal_id="1", symbol="A", strategy_name="S", ml_score=30, outcome=ResearchSignalOutcome.NEGATIVE),
        SignalJournalEntry(journal_id="2", symbol="A", strategy_name="S", ml_score=60, outcome=ResearchSignalOutcome.POSITIVE),
        SignalJournalEntry(journal_id="3", symbol="A", strategy_name="S", ml_score=90, outcome=ResearchSignalOutcome.POSITIVE)
    ]
    report = engine.build_attribution_from_journal(entries, AttributionGroupBy.ML_SCORE_BUCKET)
    assert len(report.buckets) == 3
    keys = [b.group_key for b in report.buckets]
    assert "0-40" in keys
    assert "55-70" in keys
    assert "85-100" in keys
