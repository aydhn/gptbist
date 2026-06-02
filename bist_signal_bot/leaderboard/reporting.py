import pandas as pd
from typing import Any
from bist_signal_bot.leaderboard.models import (
    BenchmarkCohort, ResearchCandidate, CandidateMetric, CandidateScore, LeaderboardEntry,
    ResearchLeaderboard, CandidateComparison, SelectionPolicy, CandidateSelectionResult, LeaderboardReport
)

def cohort_to_dict(cohort: BenchmarkCohort) -> dict[str, Any]:
    return cohort.model_dump()

def candidate_metric_to_dict(metric: CandidateMetric) -> dict[str, Any]:
    return metric.model_dump()

def candidate_to_dict(candidate: ResearchCandidate) -> dict[str, Any]:
    return candidate.model_dump()

def candidate_score_to_dict(score: CandidateScore) -> dict[str, Any]:
    return score.model_dump()

def leaderboard_entry_to_dict(entry: LeaderboardEntry) -> dict[str, Any]:
    return entry.model_dump()

def leaderboard_to_dict(leaderboard: ResearchLeaderboard) -> dict[str, Any]:
    return leaderboard.model_dump()

def comparison_to_dict(comparison: CandidateComparison) -> dict[str, Any]:
    return comparison.model_dump()

def policy_to_dict(policy: SelectionPolicy) -> dict[str, Any]:
    return policy.model_dump()

def selection_result_to_dict(result: CandidateSelectionResult) -> dict[str, Any]:
    return result.model_dump()

def leaderboard_report_to_dict(report: LeaderboardReport) -> dict[str, Any]:
    return report.model_dump()

def leaderboard_to_dataframe(leaderboard: ResearchLeaderboard) -> pd.DataFrame:
    data = []
    for entry in leaderboard.entries:
        data.append({
            "rank": entry.rank,
            "candidate_id": entry.candidate.candidate_id,
            "status": entry.score.status.value,
            "decision": entry.decision.value,
            "rank_score": entry.score.rank_score,
            "raw_score": entry.score.raw_score,
            "review_required": entry.review_required
        })
    return pd.DataFrame(data)

def candidates_to_dataframe(candidates: list[ResearchCandidate]) -> pd.DataFrame:
    data = []
    for c in candidates:
        data.append({
            "candidate_id": c.candidate_id,
            "type": c.candidate_type.value,
            "status": c.status.value,
            "metrics_count": len(c.metrics)
        })
    return pd.DataFrame(data)

def format_cohort_text(cohort: BenchmarkCohort) -> str:
    lines = [
        f"Benchmark Cohort: {cohort.name} ({cohort.cohort_id})",
        f"Type: {cohort.cohort_type.value}",
        f"Candidates: {len(cohort.candidate_ids)}",
        f"Disclaimer: {cohort.disclaimer}"
    ]
    return "\n".join(lines)

def format_candidate_text(candidate: ResearchCandidate) -> str:
    lines = [
        f"Research Candidate: {candidate.name} ({candidate.candidate_id})",
        f"Type: {candidate.candidate_type.value}",
        f"Status: {candidate.status.value}",
        f"Disclaimer: {candidate.disclaimer}"
    ]
    return "\n".join(lines)

def format_leaderboard_text(leaderboard: ResearchLeaderboard) -> str:
    lines = [
        f"Research Leaderboard: {leaderboard.leaderboard_id}",
        f"Cohort: {leaderboard.cohort_id}",
        f"Status: {leaderboard.status.value}",
        f"Top Candidate: {leaderboard.top_candidate_id or 'None'}",
        f"Disclaimer: {leaderboard.disclaimer}",
        "\nRankings:"
    ]
    for e in leaderboard.entries:
        rs = f"{e.score.rank_score:.2f}" if e.score.rank_score is not None else "N/A"
        lines.append(f"  {e.rank}. {e.candidate.candidate_id} | Score: {rs} | Status: {e.score.status.value} | Decision: {e.decision.value}")
    return "\n".join(lines)

def format_comparison_text(comparison: CandidateComparison) -> str:
    lines = [
        f"Candidate Comparison: {comparison.candidate_a_id} vs {comparison.candidate_b_id}",
        f"Winner: {comparison.winner_candidate_id or 'Tie/None'}",
        f"Decision: {comparison.decision.value}",
        f"Disclaimer: {comparison.disclaimer}"
    ]
    return "\n".join(lines)

def format_selection_result_text(result: CandidateSelectionResult) -> str:
    lines = [
        f"Selection Result: {result.selection_id}",
        f"Policy: {result.policy_id}",
        f"Selected: {len(result.selected_candidate_ids)}",
        f"Watched: {len(result.watch_candidate_ids)}",
        f"Rejected: {len(result.rejected_candidate_ids)}",
        f"Review Req: {len(result.review_required_ids)}",
        f"Disclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_leaderboard_report_markdown(report: LeaderboardReport) -> str:
    md = [
        f"# Research Leaderboard Report",
        f"Generated: {report.generated_at.isoformat()}",
        f"\n**DISCLAIMER:** {report.disclaimer}\n"
    ]

    if report.leaderboards:
        md.append("## Latest Leaderboards\n")
        for lb in report.leaderboards:
            md.append(f"### Leaderboard: {lb.leaderboard_id}")
            md.append(f"- Top Candidate: {lb.top_candidate_id or 'None'}")
            md.append(f"- Status: {lb.status.value}")
            md.append(f"- Entries: {len(lb.entries)}")
            md.append("")

            md.append("| Rank | Candidate | Score | Status | Decision |")
            md.append("|---|---|---|---|---|")
            for e in lb.entries:
                rs = f"{e.score.rank_score:.2f}" if e.score.rank_score is not None else "N/A"
                md.append(f"| {e.rank} | {e.candidate.candidate_id} | {rs} | {e.score.status.value} | {e.decision.value} |")
            md.append("")

    if report.selections:
        md.append("## Selection Results\n")
        for sel in report.selections:
            md.append(f"### Selection: {sel.selection_id}")
            md.append(f"- Policy: {sel.policy_id}")
            md.append(f"- Selected Count: {len(sel.selected_candidate_ids)}")
            md.append(f"- Watched Count: {len(sel.watch_candidate_ids)}")
            md.append(f"- Rejected Count: {len(sel.rejected_candidate_ids)}")
            md.append(f"- Review Required: {len(sel.review_required_ids)}")
            md.append("")

    return "\n".join(md)

def render_leaderboard_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_ldr",
        "section_key": "leaderboard",
        "title": "Leaderboard Report",
        "content_markdown": "*Leaderboard summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
