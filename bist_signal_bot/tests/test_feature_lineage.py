from bist_signal_bot.feature_store.lineage import FeatureLineageTracker

def test_feature_lineage():
    tracker = FeatureLineageTracker()
    tracker.link_dataset_to_feature("ds1", "feat1")
    edges = tracker.feature_lineage("feat1")
    assert len(edges) == 1
