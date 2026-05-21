import pytest
from bist_signal_bot.review.journal import DecisionJournal
from bist_signal_bot.review.storage import ReviewStore
from bist_signal_bot.review.models import ReviewDecision, ReviewDecisionType, ReviewItemStatus, ReviewItem, ReviewItemSource
from datetime import datetime, timezone
import uuid

@pytest.fixture
def store(tmp_path):
    return ReviewStore(base_dir=tmp_path)

@pytest.fixture
def journal(store):
    return DecisionJournal(store=store)

def test_journal_append(journal):
    item = ReviewItem(item_id="i1", source=ReviewItemSource.MANUAL, symbol="ASELS", title="T", summary="S", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    decision = ReviewDecision(decision_id="d1", item_id="i1", decision_type=ReviewDecisionType.WATCH_ONLY, new_status=ReviewItemStatus.WATCH_ONLY, decided_at=datetime.now(timezone.utc), reason="r")

    entry = journal.append_from_decision(decision, item)
    assert entry.symbol == "ASELS"

    entries = journal.list_entries(symbol="ASELS")
    assert len(entries) == 1
