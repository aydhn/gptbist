from bist_signal_bot.review.inbox import ReviewInboxManager
def test_review_inbox_disclosure_hook():
    mgr = ReviewInboxManager()
    class MockSignal:
        symbol = "ASELS"
        metadata = {"disclosures": {"REQUIRE_REVIEW": True}}
    item = mgr.add_item_from_signal(MockSignal())
    assert item.symbol == "ASELS"
