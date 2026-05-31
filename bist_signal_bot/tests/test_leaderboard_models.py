import pytest
from datetime import datetime
from bist_signal_bot.leaderboard.models import (
    LeaderboardStatus, CandidateType, CandidateDecision, BenchmarkCohortType,
    RankingMetricName, BenchmarkCohort, CandidateMetric, ResearchCandidate,
    CandidateScore, LeaderboardEntry, ResearchLeaderboard, CandidateComparison,
    SelectionPolicy, CandidateSelectionResult, LeaderboardReport
)

def test_benchmark_cohort_disclaimer():
    cohort = BenchmarkCohort(
        cohort_id="test_cohort",
        cohort_type=BenchmarkCohortType.STRATEGY_COHORT,
        name="Test Cohort",
        description="A test cohort",
        candidate_type=CandidateType.STRATEGY
    )
    assert "It is not investment advice or permission to trade." in cohort.disclaimer

def test_research_candidate_disclaimer():
    candidate = ResearchCandidate(
        candidate_id="test_candidate",
        candidate_type=CandidateType.STRATEGY,
        name="Test Candidate"
    )
    assert "It is not investment advice, recommendation, or order instruction." in candidate.disclaimer

def test_candidate_metric_defaults():
    metric = CandidateMetric(
        metric_id="test_metric",
        candidate_type=CandidateType.STRATEGY,
        candidate_id="test_candidate",
        metric_name=RankingMetricName.VALIDATION_SCORE
    )
    assert metric.weight == 1.0
    assert metric.direction == "HIGHER_IS_BETTER"
    assert metric.status == LeaderboardStatus.UNKNOWN

def test_leaderboard_report_disclaimer():
    report = LeaderboardReport(report_id="test_report")
    assert "It is not investment advice or permission to trade." in report.disclaimer
