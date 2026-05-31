from pathlib import Path
from bist_signal_bot.leaderboard.storage import LeaderboardStore
from bist_signal_bot.leaderboard.cohorts import BenchmarkCohortBuilder
from bist_signal_bot.leaderboard.collectors import LeaderboardDataCollector
from bist_signal_bot.leaderboard.scoring import CandidateScoringEngine
from bist_signal_bot.leaderboard.ranking import CandidateRankingEngine
from bist_signal_bot.leaderboard.comparison import CandidateComparisonEngine
from bist_signal_bot.leaderboard.policy import SelectionPolicyRegistry
from bist_signal_bot.leaderboard.selection import CandidateSelectionEngine

def create_leaderboard_store(settings=None, base_dir: Path | None = None) -> LeaderboardStore:
    return LeaderboardStore(settings=settings, base_dir=base_dir)

def create_benchmark_cohort_builder(settings=None, base_dir: Path | None = None) -> BenchmarkCohortBuilder:
    return BenchmarkCohortBuilder(settings=settings)

def create_leaderboard_data_collector(settings=None, base_dir: Path | None = None) -> LeaderboardDataCollector:
    return LeaderboardDataCollector(settings=settings)

def create_candidate_scoring_engine(settings=None, base_dir: Path | None = None) -> CandidateScoringEngine:
    return CandidateScoringEngine(settings=settings)

def create_candidate_ranking_engine(settings=None, base_dir: Path | None = None) -> CandidateRankingEngine:
    scoring_engine = create_candidate_scoring_engine(settings=settings, base_dir=base_dir)
    return CandidateRankingEngine(scoring_engine=scoring_engine, settings=settings)

def create_candidate_comparison_engine(settings=None, base_dir: Path | None = None) -> CandidateComparisonEngine:
    scoring_engine = create_candidate_scoring_engine(settings=settings, base_dir=base_dir)
    return CandidateComparisonEngine(scoring_engine=scoring_engine, settings=settings)

def create_selection_policy_registry(settings=None, base_dir: Path | None = None) -> SelectionPolicyRegistry:
    return SelectionPolicyRegistry(settings=settings)

def create_candidate_selection_engine(settings=None, base_dir: Path | None = None) -> CandidateSelectionEngine:
    return CandidateSelectionEngine(settings=settings)
