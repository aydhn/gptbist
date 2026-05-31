import pytest
from bist_signal_bot.leaderboard.storage import LeaderboardStore
from bist_signal_bot.leaderboard.models import BenchmarkCohort, BenchmarkCohortType, CandidateType, SelectionPolicy
from bist_signal_bot.config.settings import Settings

def test_leaderboard_storage_cohort(tmp_path):
    store = LeaderboardStore(settings=Settings(), base_dir=tmp_path)
    cohort = BenchmarkCohort(
        cohort_id="c1", cohort_type=BenchmarkCohortType.STRATEGY_COHORT, name="C1", description="desc", candidate_type=CandidateType.STRATEGY
    )
    p = store.append_cohort(cohort)
    assert p.exists()
    cohorts = store.load_cohorts()
    assert len(cohorts) == 1
    assert cohorts[0].cohort_id == "c1"

def test_leaderboard_storage_policies(tmp_path):
    store = LeaderboardStore(settings=Settings(), base_dir=tmp_path)
    p1 = SelectionPolicy(policy_id="p1", name="P1", version="1.0", candidate_type=CandidateType.STRATEGY)
    p = store.save_policies([p1])
    assert p.exists()
    policies = store.load_policies()
    assert len(policies) == 1
    assert policies[0].policy_id == "p1"
