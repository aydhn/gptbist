from typing import Any
from bist_signal_bot.leaderboard.models import SelectionPolicy, CandidateType
from bist_signal_bot.core.exceptions import SelectionPolicyError

class SelectionPolicyRegistry:
    def __init__(self, settings=None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self._policies: dict[str, SelectionPolicy] = {}
        for p in self.default_policies():
            self._policies[p.policy_id] = p

    def default_policies(self) -> list[SelectionPolicy]:
        weights = {
            "VALIDATION_SCORE": self.settings.LEADERBOARD_WEIGHT_VALIDATION_SCORE,
            "CALIBRATION_SCORE": self.settings.LEADERBOARD_WEIGHT_CALIBRATION_SCORE,
            "MONITORING_HEALTH": self.settings.LEADERBOARD_WEIGHT_MONITORING_HEALTH,
            "ROBUSTNESS_SCORE": self.settings.LEADERBOARD_WEIGHT_ROBUSTNESS_SCORE,
            "FEATURE_QUALITY": self.settings.LEADERBOARD_WEIGHT_FEATURE_QUALITY,
            "MODEL_GOVERNANCE": self.settings.LEADERBOARD_WEIGHT_MODEL_GOVERNANCE,
            "CONTEXT_SUPPORT": self.settings.LEADERBOARD_WEIGHT_CONTEXT_SUPPORT,
            "REVIEW_BURDEN": self.settings.LEADERBOARD_WEIGHT_REVIEW_BURDEN,
            "DATA_QUALITY": self.settings.LEADERBOARD_WEIGHT_DATA_QUALITY
        }

        normalized_weights = self.normalize_weights(weights)

        return [
            SelectionPolicy(
                policy_id="strategy_research_selection_v1",
                name="Strategy Research Selection V1",
                version="1.0",
                candidate_type=CandidateType.STRATEGY,
                min_rank_score=self.settings.LEADERBOARD_SELECTION_MIN_SCORE,
                min_sample_count=self.settings.LEADERBOARD_SELECTION_MIN_SAMPLE,
                block_on_leakage=self.settings.LEADERBOARD_SELECTION_BLOCK_ON_LEAKAGE,
                block_on_governance_fail=self.settings.LEADERBOARD_SELECTION_BLOCK_ON_GOVERNANCE_FAIL,
                weights=normalized_weights
            ),
            SelectionPolicy(
                policy_id="model_research_selection_v1",
                name="Model Research Selection V1",
                version="1.0",
                candidate_type=CandidateType.MODEL,
                min_rank_score=self.settings.LEADERBOARD_SELECTION_MIN_SCORE,
                min_sample_count=self.settings.LEADERBOARD_SELECTION_MIN_SAMPLE,
                block_on_leakage=self.settings.LEADERBOARD_SELECTION_BLOCK_ON_LEAKAGE,
                require_model_card=True,
                weights=normalized_weights
            ),
            SelectionPolicy(
                policy_id="feature_set_research_selection_v1",
                name="Feature Set Research Selection V1",
                version="1.0",
                candidate_type=CandidateType.FEATURE_SET,
                min_rank_score=self.settings.LEADERBOARD_SELECTION_MIN_SCORE,
                block_on_leakage=True,
                weights=normalized_weights
            ),
            SelectionPolicy(
                policy_id="portfolio_research_selection_v1",
                name="Portfolio Research Selection V1",
                version="1.0",
                candidate_type=CandidateType.PORTFOLIO_RESEARCH,
                min_rank_score=self.settings.LEADERBOARD_SELECTION_MIN_SCORE,
                weights=normalized_weights
            ),
            SelectionPolicy(
                policy_id="conservative_research_selection_v1",
                name="Conservative Research Selection V1",
                version="1.0",
                candidate_type=CandidateType.CUSTOM,
                min_rank_score=self.settings.LEADERBOARD_SCORE_PASS_THRESHOLD,
                min_sample_count=100,
                block_on_leakage=True,
                block_on_governance_fail=True,
                block_on_data_quality_fail=True,
                require_monitoring_pass=True,
                require_calibration_pass=True,
                weights=normalized_weights
            )
        ]

    def get_policy(self, policy_id_or_name: str) -> SelectionPolicy | None:
        if policy_id_or_name in self._policies:
            return self._policies[policy_id_or_name]
        for p in self._policies.values():
            if p.name == policy_id_or_name:
                return p
        return None

    def validate_policy(self, policy: SelectionPolicy) -> list[str]:
        warnings = []
        if not policy.weights:
            warnings.append("Policy has empty weights.")
        if any(w < 0 for w in policy.weights.values()):
            warnings.append("Policy contains negative weights.")
        total = sum(policy.weights.values())
        if abs(total - 1.0) > 0.01:
            warnings.append(f"Policy weights do not sum to 1.0 (sum={total}).")
        return warnings

    def normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        if not weights:
            return {}
        total = sum(v for v in weights.values() if v > 0)
        if total <= 0:
            return {k: 1.0 / len(weights) for k in weights}
        return {k: (v / total if v > 0 else 0.0) for k, v in weights.items()}

    def policy_for_candidate_type(self, candidate_type: CandidateType) -> SelectionPolicy:
        for p in self._policies.values():
            if p.candidate_type == candidate_type:
                return p
        return self._policies["conservative_research_selection_v1"]
