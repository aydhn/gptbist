def test_qa_integration():
    from bist_signal_bot.qa.release_gate import run_release_gate
    res = run_release_gate(include_feature_store=True)
    assert "feature_store" in res
