import pytest
from bist_signal_bot.leaderboard.scoring import CandidateScoringEngine
from bist_signal_bot.leaderboard.models import ResearchCandidate, CandidateType, CandidateMetric, RankingMetricName, LeaderboardStatus
from bist_signal_bot.config.settings import Settings

def test_scoring_weighted_raw_score():
    engine = CandidateScoringEngine(settings=Settings())
    metrics = [
        CandidateMetric(metric_id="m1", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.VALIDATION_SCORE, value=80.0),
        CandidateMetric(metric_id="m2", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.CALIBRATION_SCORE, value=60.0)
    ]
    weights = {"VALIDATION_SCORE": 0.5, "CALIBRATION_SCORE": 0.5}
    raw = engine.weighted_raw_score(metrics, weights)
    assert raw == 70.0

def test_scoring_low_sample_penalty():
    engine = CandidateScoringEngine(settings=Settings())
    candidate = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    candidate.metrics = [
        CandidateMetric(metric_id="m1", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.VALIDATION_SCORE, value=80.0, sample_count=10)
    ]
    score = engine.score_candidate(candidate)
    assert "low_sample_penalty" in score.penalties

def test_scoring_leakage_penalty():
    engine = CandidateScoringEngine(settings=Settings())
    candidate = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1", warnings=["Leakage detected"])
    candidate.metrics = [
        CandidateMetric(metric_id="m1", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.VALIDATION_SCORE, value=80.0, sample_count=100)
    ]
    score = engine.score_candidate(candidate)
    assert "leakage_penalty" in score.penalties

def test_scoring_clamp():
    engine = CandidateScoringEngine(settings=Settings())
    candidate = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    candidate.metrics = [
        CandidateMetric(metric_id="m1", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.VALIDATION_SCORE, value=150.0, sample_count=100)
    ]
    score = engine.score_candidate(candidate)
    assert score.adjusted_score == 100.0
