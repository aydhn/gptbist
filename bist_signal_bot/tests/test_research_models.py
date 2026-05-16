import pytest
from datetime import datetime
from bist_signal_bot.research.models import (
    ResearchRun, ResearchRunType, ResearchRunStatus, ResearchTag,
    ResearchArtifactRef, ResearchArtifactType, SignalJournalEntry,
    ResearchSignalOutcome, ResearchComparisonReport, ResearchComparisonItem,
    AttributionReport, AttributionBucket, AttributionGroupBy, ResearchQuery,
    ResearchNote
)

def test_research_run_validation():
    run = ResearchRun(
        run_id="test_run",
        run_type=ResearchRunType.BACKTEST,
        status=ResearchRunStatus.SUCCESS,
        title="Test Title",
        started_at=datetime.utcnow()
    )
    assert run.title == "Test Title"
    summary = run.summary()
    assert summary["run_id"] == "test_run"

def test_research_tag_validation():
    tag = ResearchTag(tag="valid-tag")
    assert tag.tag == "valid-tag"
    with pytest.raises(ValueError, match="empty"):
        ResearchTag(tag="")
    with pytest.raises(ValueError, match="forbidden"):
        ResearchTag(tag="secret-token")

def test_research_artifact_ref_validation():
    ref = ResearchArtifactRef(
        artifact_id="art1",
        artifact_type=ResearchArtifactType.JSON,
        path="valid/path.json"
    )
    assert ref.path == "valid/path.json"
    with pytest.raises(ValueError, match="Unsafe path"):
        ResearchArtifactRef(artifact_id="art2", artifact_type=ResearchArtifactType.JSON, path="/etc/passwd")

def test_signal_journal_entry():
    entry = SignalJournalEntry(
        journal_id="j1",
        symbol="ASELS",
        strategy_name="s1"
    )
    assert entry.outcome == ResearchSignalOutcome.NOT_TRACKED
    summary = entry.summary()
    assert summary["symbol"] == "ASELS"

def test_research_note_validation():
    note = ResearchNote(note_id="n1", title="Title", body="Normal note")
    assert note.title == "Title"
    with pytest.raises(ValueError, match="empty"):
         ResearchNote(note_id="n2", title="", body="body")
    with pytest.raises(ValueError, match="unsafe financial claims"):
         ResearchNote(note_id="n3", title="t", body="guaranteed profit today!")

def test_research_query_validation():
    q = ResearchQuery(limit=5)
    assert q.limit == 5
    with pytest.raises(ValueError, match="positive"):
        ResearchQuery(limit=0)
