from bist_signal_bot.review_workflow.checklist import ReviewChecklistBuilder
from bist_signal_bot.review_workflow.playbooks import ReviewPlaybookRegistry
from bist_signal_bot.review_workflow.models import ChecklistItemStatus

def test_build_standard_checklist():
    builder = ReviewChecklistBuilder()
    items = builder.standard_signal_items("case-1")
    assert len(items) == 4
    assert items[0].title == "Context Snapshot Up-to-date"

def test_build_playbook_checklist():
    builder = ReviewChecklistBuilder()
    registry = ReviewPlaybookRegistry()
    playbooks = registry.select_playbooks(conflicts=["MACRO_PRESSURE"])
    items = builder.build_checklist("case-1", playbooks)
    assert len(items) > 4
    assert any(item.title == "Macro Pressure Check" for item in items)

def test_completion_rate():
    builder = ReviewChecklistBuilder()
    items = builder.standard_signal_items("case-1")
    items[0].status = ChecklistItemStatus.PASSED
    rate = builder.completion_rate(items)
    assert rate == 25.0
