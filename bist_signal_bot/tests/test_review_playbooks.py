from bist_signal_bot.review_workflow.playbooks import ReviewPlaybookRegistry

def test_default_playbooks():
    registry = ReviewPlaybookRegistry()
    playbooks = registry.default_playbooks()
    assert len(playbooks) == 13
    assert any(pb.playbook_type.name == "MACRO_PRESSURE" for pb in playbooks)

def test_select_playbooks_by_conflict():
    registry = ReviewPlaybookRegistry()
    playbooks = registry.select_playbooks(conflicts=["MACRO_PRESSURE"])
    assert len(playbooks) == 1
    assert playbooks[0].playbook_type.name == "MACRO_PRESSURE"

def test_select_playbooks_by_gaps():
    registry = ReviewPlaybookRegistry()
    playbooks = registry.select_playbooks(gaps=["some_gap"])
    assert len(playbooks) == 1
    assert playbooks[0].playbook_type.name == "MISSING_DATA"

def test_select_playbooks_default():
    registry = ReviewPlaybookRegistry()
    playbooks = registry.select_playbooks()
    assert len(playbooks) == 1
    assert playbooks[0].playbook_type.name == "STANDARD_SIGNAL_REVIEW"
