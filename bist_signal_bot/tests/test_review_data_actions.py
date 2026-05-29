from bist_signal_bot.review_workflow.data_actions import ReviewDataActionQueue

def test_create_action():
    queue = ReviewDataActionQueue()
    action = queue.create_action("case-1", "Fetch macro")
    assert action.action_type == "FETCH_DATA"
    assert action.description == "Fetch macro"

def test_create_actions_from_gaps():
    queue = ReviewDataActionQueue()
    actions = queue.create_actions_from_gaps("case-1", ["macro", "breadth"])
    assert len(actions) == 2
    assert actions[0].evidence_gap_id == "macro"

def test_resolve_action():
    queue = ReviewDataActionQueue()
    action = queue.resolve_action("act-1", "Resolved")
    assert action.status == "RESOLVED"
    assert action.metadata["resolution_note"] == "Resolved"
