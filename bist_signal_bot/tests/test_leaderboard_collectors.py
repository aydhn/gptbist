import pytest
from bist_signal_bot.leaderboard.collectors import LeaderboardDataCollector
from bist_signal_bot.leaderboard.models import CandidateType, RankingMetricName

def test_leaderboard_collector_missing_source(mocker):
    mock_settings = mocker.Mock()
    collector = LeaderboardDataCollector(settings=mock_settings)
    candidate = collector.collect_strategy_candidate("strategy_x")
    val_metric = next(m for m in candidate.metrics if m.metric_name == RankingMetricName.VALIDATION_SCORE)
    assert "Missing source" in val_metric.warnings

def test_leaderboard_collector_strategy(mocker):
    collector = LeaderboardDataCollector(settings=mocker.Mock())
    candidate = collector.collect_candidate(CandidateType.STRATEGY, "strat_a")
    assert candidate.candidate_type == CandidateType.STRATEGY

def test_leaderboard_collector_model_gov(mocker):
    collector = LeaderboardDataCollector(settings=mocker.Mock())
    candidate = collector.collect_candidate(CandidateType.MODEL, "model_b")
    assert any(m.metric_name == RankingMetricName.MODEL_GOVERNANCE for m in candidate.metrics)
