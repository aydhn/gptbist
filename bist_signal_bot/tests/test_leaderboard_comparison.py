import pytest
from bist_signal_bot.leaderboard.comparison import CandidateComparisonEngine
from bist_signal_bot.leaderboard.models import ResearchCandidate, CandidateType, CandidateMetric, RankingMetricName, CandidateDecision

def test_comparison_metric_deltas(mocker):
    engine = CandidateComparisonEngine(settings=mocker.Mock())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    c1.metrics = [CandidateMetric(metric_id="m1", candidate_type=CandidateType.STRATEGY, candidate_id="c1", metric_name=RankingMetricName.VALIDATION_SCORE, value=80.0)]
    c2 = ResearchCandidate(candidate_id="c2", candidate_type=CandidateType.STRATEGY, name="C2")
    c2.metrics = [CandidateMetric(metric_id="m2", candidate_type=CandidateType.STRATEGY, candidate_id="c2", metric_name=RankingMetricName.VALIDATION_SCORE, value=75.0)]
    deltas = engine.metric_deltas(c1, c2)
    assert deltas["VALIDATION_SCORE"] == 5.0

def test_comparison_low_sample_needs_more_data(mocker):
    engine = CandidateComparisonEngine(settings=mocker.Mock())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    c2 = ResearchCandidate(candidate_id="c2", candidate_type=CandidateType.STRATEGY, name="C2")
    comp = engine.compare(c1, c2)
    assert comp.decision == CandidateDecision.NEEDS_MORE_DATA
