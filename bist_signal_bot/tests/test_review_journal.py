from bist_signal_bot.review_workflow.journal import DecisionJournal

def test_append_entry():
    journal = DecisionJournal()
    entry = journal.append_entry("case-1", "Test note", "analyst")
    assert entry.case_id == "case-1"
    assert entry.note == "Test note"
    assert entry.actor == "analyst"

def test_append_entry_trade_language_block():
    journal = DecisionJournal()
    entry = journal.append_entry("case-1", "trade approved for ASELS")
    assert "[REDACTED_UNSAFE_CLAIM]" in entry.note

def test_correction_entry():
    journal = DecisionJournal()
    entry = journal.correct_entry("entry-1", "Fixed note")
    assert entry.correction_of == "entry-1"
    assert entry.entry_type == "CORRECTION"
    assert "Fixed note" in entry.note
