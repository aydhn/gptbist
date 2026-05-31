import pytest
from bist_signal_bot.leaderboard.cohorts import BenchmarkCohortBuilder
from bist_signal_bot.leaderboard.models import BenchmarkCohortType, CandidateType

def test_benchmark_cohort_validation_empty_warning(mocker):
    mock_settings = mocker.Mock()
    mock_settings.LEADERBOARD_MIN_CANDIDATES = 2
    builder = BenchmarkCohortBuilder(settings=mock_settings)
    cohort = builder.build_strategy_cohort(strategy_names=[])
    assert any("INSUFFICIENT_DATA" in w for w in cohort.warnings)

def test_cohort_builder_strategy(mocker):
    mock_settings = mocker.Mock()
    mock_settings.LEADERBOARD_MIN_CANDIDATES = 2
    builder = BenchmarkCohortBuilder(settings=mock_settings)
    cohort = builder.build_strategy_cohort(strategy_names=["b", "a", "a"])
    assert cohort.cohort_type == BenchmarkCohortType.STRATEGY_COHORT
    assert cohort.candidate_type == CandidateType.STRATEGY
    assert cohort.candidate_ids == ["a", "b"]

def test_cohort_builder_model(mocker):
    mock_settings = mocker.Mock()
    mock_settings.LEADERBOARD_MIN_CANDIDATES = 2
    builder = BenchmarkCohortBuilder(settings=mock_settings)
    cohort = builder.build_model_cohort(model_ids=["m1", "m2"])
    assert cohort.cohort_type == BenchmarkCohortType.MODEL_COHORT
    assert cohort.candidate_type == CandidateType.MODEL

def test_cohort_builder_feature_set(mocker):
    mock_settings = mocker.Mock()
    mock_settings.LEADERBOARD_MIN_CANDIDATES = 2
    builder = BenchmarkCohortBuilder(settings=mock_settings)
    cohort = builder.build_feature_set_cohort(feature_set_ids=["f1"])
    assert cohort.cohort_type == BenchmarkCohortType.FEATURE_SET_COHORT
    assert cohort.candidate_type == CandidateType.FEATURE_SET
