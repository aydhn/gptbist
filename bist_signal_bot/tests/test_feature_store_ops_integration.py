def test_ops_integration():
    from bist_signal_bot.ops.readiness import check_readiness
    res = check_readiness(include_feature_store=True)
    assert "feature_store" in res
