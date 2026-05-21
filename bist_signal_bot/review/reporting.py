import pandas as pd
from typing import List, Any, Dict

from .models import (
    ReviewItem, ReviewEvidence, ReviewChecklist, ReviewThesis,
    ReviewDecision, DecisionJournalEntry, ReviewInboxSummary
)

def review_item_to_dict(item: ReviewItem) -> Dict[str, Any]:
    return item.safe_public_dict()

def review_evidence_to_dict(evidence: ReviewEvidence) -> Dict[str, Any]:
    return evidence.model_dump(mode="json")

def review_checklist_to_dict(checklist: ReviewChecklist) -> Dict[str, Any]:
    return checklist.model_dump(mode="json")

def review_thesis_to_dict(thesis: ReviewThesis) -> Dict[str, Any]:
    return thesis.model_dump(mode="json")

def review_decision_to_dict(decision: ReviewDecision) -> Dict[str, Any]:
    return decision.model_dump(mode="json")

def journal_entry_to_dict(entry: DecisionJournalEntry) -> Dict[str, Any]:
    return entry.model_dump(mode="json")

def review_items_to_dataframe(items: List[ReviewItem]) -> pd.DataFrame:
    data = [item.summary_dict() for item in items]
    return pd.DataFrame(data)

def review_decisions_to_dataframe(decisions: List[ReviewDecision]) -> pd.DataFrame:
    data = [d.model_dump(mode="json") for d in decisions]
    return pd.DataFrame(data)

def format_review_item_text(item: ReviewItem) -> str:
    lines = [
        f"Review Item: {item.title}",
        f"Symbol: {item.symbol}",
        f"Status: {item.status.value}",
        f"Source: {item.source.value}",
        f"Summary: {item.summary}",
        f"Disclaimer: {item.disclaimer}"
    ]
    return "\n".join(lines)

def format_review_inbox_summary(summary: ReviewInboxSummary) -> str:
    lines = [
        "Analyst Review Inbox Summary",
        f"Total: {summary.total_items}",
        f"New: {summary.new_count}",
        f"In Review: {summary.in_review_count}",
        f"Approved Research: {summary.approved_research_count}",
        f"Watch Only: {summary.watch_only_count}",
        f"Rejected: {summary.rejected_count}"
    ]
    return "\n".join(lines)

def format_review_checklist_text(checklist: ReviewChecklist) -> str:
    lines = [f"Checklist Status: {checklist.overall_status.value}"]
    for item in checklist.items:
        lines.append(f"- {item.name}: {item.status.value}")
    return "\n".join(lines)

def format_review_thesis_text(thesis: ReviewThesis) -> str:
    lines = [
        f"Symbol: {thesis.symbol}",
        f"Main Thesis: {thesis.main_thesis}",
        f"Counter Thesis: {thesis.counter_thesis}",
        f"Disclaimer: {thesis.disclaimer}"
    ]
    return "\n".join(lines)

def format_review_decision_text(decision: ReviewDecision) -> str:
    lines = [
        f"Decision: {decision.decision_type.value}",
        f"Reason: {decision.reason}",
        f"Disclaimer: {decision.disclaimer}"
    ]
    return "\n".join(lines)

def format_decision_journal_text(entries: List[DecisionJournalEntry]) -> str:
    if not entries:
        return "No journal entries found."
    lines = ["Decision Journal:"]
    for e in entries:
        lines.append(f"- {e.symbol} [{e.created_at.date()}]: {e.decision_type.value}")
    return "\n".join(lines)

def format_review_report_markdown(items: List[ReviewItem], summary: ReviewInboxSummary) -> str:
    lines = [
        "# Analyst Review Report",
        "> " + items[0].disclaimer if items else "> Research-only",
        "",
        format_review_inbox_summary(summary),
        "",
        "## Top Items"
    ]
    for item in items[:10]:
        lines.append(f"### {item.symbol}")
        lines.append(f"- Status: {item.status.value}")
        lines.append(f"- Summary: {item.summary}")
    return "\n".join(lines)
