import uuid
from datetime import datetime
from typing import Any
from bist_signal_bot.leaderboard.models import (
    BenchmarkCohort, BenchmarkCohortType, CandidateType
)
from bist_signal_bot.core.exceptions import BenchmarkCohortError

class BenchmarkCohortBuilder:
    def __init__(self, settings=None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()

    def build_strategy_cohort(self, strategy_names: list[str] | None = None, as_of: datetime | None = None) -> BenchmarkCohort:
        if strategy_names is None:
            strategy_names = []

        cohort = BenchmarkCohort(
            cohort_id=f"cohort_strat_{uuid.uuid4().hex[:8]}",
            cohort_type=BenchmarkCohortType.STRATEGY_COHORT,
            name="Strategy Research Cohort",
            description="Benchmark cohort for comparing strategy candidates.",
            candidate_type=CandidateType.STRATEGY,
            candidate_ids=sorted(list(set(strategy_names))),
            as_of=as_of or datetime.now()
        )
        self._validate_and_warn(cohort)
        return cohort

    def build_model_cohort(self, model_ids: list[str] | None = None, as_of: datetime | None = None) -> BenchmarkCohort:
        if model_ids is None:
            model_ids = []

        cohort = BenchmarkCohort(
            cohort_id=f"cohort_mod_{uuid.uuid4().hex[:8]}",
            cohort_type=BenchmarkCohortType.MODEL_COHORT,
            name="Model Research Cohort",
            description="Benchmark cohort for comparing ML models.",
            candidate_type=CandidateType.MODEL,
            candidate_ids=sorted(list(set(model_ids))),
            as_of=as_of or datetime.now()
        )
        self._validate_and_warn(cohort)
        return cohort

    def build_feature_set_cohort(self, feature_set_ids: list[str] | None = None, as_of: datetime | None = None) -> BenchmarkCohort:
        if feature_set_ids is None:
            feature_set_ids = []

        cohort = BenchmarkCohort(
            cohort_id=f"cohort_feat_{uuid.uuid4().hex[:8]}",
            cohort_type=BenchmarkCohortType.FEATURE_SET_COHORT,
            name="Feature Set Research Cohort",
            description="Benchmark cohort for comparing feature sets.",
            candidate_type=CandidateType.FEATURE_SET,
            candidate_ids=sorted(list(set(feature_set_ids))),
            as_of=as_of or datetime.now()
        )
        self._validate_and_warn(cohort)
        return cohort

    def build_mixed_research_cohort(self, candidate_refs: list[dict[str, str]], as_of: datetime | None = None) -> BenchmarkCohort:
        candidate_ids = [ref.get("id") for ref in candidate_refs if "id" in ref]

        cohort = BenchmarkCohort(
            cohort_id=f"cohort_mix_{uuid.uuid4().hex[:8]}",
            cohort_type=BenchmarkCohortType.MIXED_RESEARCH_COHORT,
            name="Mixed Research Cohort",
            description="Benchmark cohort for comparing mixed research candidates.",
            candidate_type=CandidateType.CUSTOM,
            candidate_ids=sorted(list(set(candidate_ids))),
            as_of=as_of or datetime.now(),
            metadata={"refs": candidate_refs}
        )
        self._validate_and_warn(cohort)
        return cohort

    def default_cohorts(self) -> list[BenchmarkCohort]:
        cohorts = []
        if self.settings.LEADERBOARD_DEFAULT_STRATEGY_COHORT:
            cohorts.append(self.build_strategy_cohort())
        if self.settings.LEADERBOARD_DEFAULT_MODEL_COHORT:
            cohorts.append(self.build_model_cohort())
        if self.settings.LEADERBOARD_DEFAULT_FEATURE_SET_COHORT:
            cohorts.append(self.build_feature_set_cohort())
        return cohorts

    def validate_cohort(self, cohort: BenchmarkCohort) -> list[str]:
        warnings = []
        if not cohort.candidate_ids:
            warnings.append("INSUFFICIENT_DATA: Empty cohort, no candidates provided.")
        if len(cohort.candidate_ids) < self.settings.LEADERBOARD_MIN_CANDIDATES:
            warnings.append(f"INSUFFICIENT_DATA: Less than {self.settings.LEADERBOARD_MIN_CANDIDATES} candidates in cohort.")
        return warnings

    def _validate_and_warn(self, cohort: BenchmarkCohort):
        cohort.warnings.extend(self.validate_cohort(cohort))
