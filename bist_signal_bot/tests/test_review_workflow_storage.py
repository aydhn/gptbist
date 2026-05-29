from pathlib import Path
from bist_signal_bot.review_workflow.storage import ReviewWorkflowStore
from bist_signal_bot.review_workflow.models import ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority, DecisionJournalEntry

def test_store_append_load_case(tmp_path):
    store = ReviewWorkflowStore(tmp_path)
    case = ReviewCase(
        case_id="c1",
        title="T",
        summary="S",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.MEDIUM,
        symbol="ASELS"
    )
    store.append_case(case)

    cases = store.load_cases(symbol="ASELS")
    assert len(cases) == 1
    assert cases[0].case_id == "c1"

def test_store_append_load_journal(tmp_path):
    store = ReviewWorkflowStore(tmp_path)
    entry = DecisionJournalEntry(
        entry_id="e1",
        case_id="c1",
        note="Test"
    )
    store.append_journal_entry(entry)

    entries = store.load_journal(case_id="c1")
    assert len(entries) == 1
    assert entries[0].note == "Test"
