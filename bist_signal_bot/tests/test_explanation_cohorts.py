from bist_signal_bot.explainability.cohorts import ExplanationCohortBuilder

class MockFrame:
    columns = ["f1", "f2"]
    index = [1, 2, 3]

def test_explanation_cohort_feature_frame():
    bld = ExplanationCohortBuilder()
    cohort = bld.cohort_from_feature_frame(MockFrame())
    assert cohort.sample_count == 3
    assert cohort.feature_names == ["f1", "f2"]
