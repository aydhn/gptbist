from datetime import datetime
from bist_signal_bot.leaderboard.models import (
    ResearchLeaderboard, SelectionPolicy, CandidateSelectionResult, LeaderboardEntry, CandidateDecision, LeaderboardStatus
)

class CandidateSelectionEngine:
    def __init__(self, settings=None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()

    def select_from_leaderboard(self, leaderboard: ResearchLeaderboard, policy: SelectionPolicy | None = None) -> CandidateSelectionResult:
        res = CandidateSelectionResult(
            selection_id=f"sel_{leaderboard.leaderboard_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            policy_id=policy.policy_id if policy else "default",
            leaderboard_id=leaderboard.leaderboard_id
        )

        for entry in leaderboard.entries:
            c_id = entry.candidate.candidate_id

            reasons = self.blocking_reasons(entry, policy)
            if reasons:
                res.blocking_reasons[c_id] = reasons
                res.rejected_candidate_ids.append(c_id)
                continue

            if self.is_selected(entry, policy):
                res.selected_candidate_ids.append(c_id)
            else:
                res.watch_candidate_ids.append(c_id)

            if self.needs_review(entry, policy):
                res.review_required_ids.append(c_id)

        res.metadata["summary"] = self.selection_summary(res)
        return res

    def blocking_reasons(self, entry: LeaderboardEntry, policy: SelectionPolicy | None = None) -> list[str]:
        reasons = []
        if entry.score.status == LeaderboardStatus.BLOCKED_RESEARCH:
            reasons.append("Blocked by base leaderboard rules.")

        if policy:
            if policy.block_on_leakage and "leakage_block" in entry.score.penalties:
                reasons.append("Blocked due to leakage policy.")
            if policy.block_on_governance_fail and any("governance" in p.lower() for p in entry.score.penalties):
                reasons.append("Blocked due to governance failure policy.")
            if policy.min_sample_count and "low_sample_penalty" in entry.score.penalties:
                reasons.append("Blocked due to minimum sample count policy.")

        return reasons

    def is_selected(self, entry: LeaderboardEntry, policy: SelectionPolicy | None = None) -> bool:
        if self.blocking_reasons(entry, policy):
            return False

        min_score = policy.min_rank_score if policy and policy.min_rank_score is not None else self.settings.LEADERBOARD_SELECTION_MIN_SCORE

        if entry.score.rank_score is not None and entry.score.rank_score >= min_score:
            return True

        return False

    def needs_review(self, entry: LeaderboardEntry, policy: SelectionPolicy | None = None) -> bool:
        return entry.review_required or (policy and policy.require_monitoring_pass and entry.score.status != LeaderboardStatus.PASS)

    def selection_summary(self, result: CandidateSelectionResult) -> list[str]:
        return [
            f"Selected: {len(result.selected_candidate_ids)}",
            f"Watched: {len(result.watch_candidate_ids)}",
            f"Rejected: {len(result.rejected_candidate_ids)}",
            f"Review Req: {len(result.review_required_ids)}"
        ]
