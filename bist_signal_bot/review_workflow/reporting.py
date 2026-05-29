# import pandas as pd
from typing import Any, List, Dict
from bist_signal_bot.review_workflow.models import (
    ReviewCase, ReviewPlaybook, ReviewChecklistItem, DecisionJournalEntry,
    ReviewSignoffRequest, ReviewDataAction, ReviewPattern, ReviewWorkflowReport
)

def playbook_to_dict(playbook: ReviewPlaybook) -> Dict[str, Any]:
    return playbook.__dict__

def checklist_item_to_dict(item: ReviewChecklistItem) -> Dict[str, Any]:
    return item.__dict__

def review_case_to_dict(case: ReviewCase) -> Dict[str, Any]:
    return case.__dict__

def journal_entry_to_dict(entry: DecisionJournalEntry) -> Dict[str, Any]:
    return entry.__dict__

def signoff_to_dict(signoff: ReviewSignoffRequest) -> Dict[str, Any]:
    return signoff.__dict__

def data_action_to_dict(action: ReviewDataAction) -> Dict[str, Any]:
    return action.__dict__

def pattern_to_dict(pattern: ReviewPattern) -> Dict[str, Any]:
    return pattern.__dict__

def workflow_report_to_dict(report: ReviewWorkflowReport) -> Dict[str, Any]:
    return report.__dict__

def cases_to_dataframe(cases: List[ReviewCase]) -> Any:
    data = []
    for c in cases:
        data.append({
            "case_id": c.case_id,
            "symbol": c.symbol,
            "status": c.status.name,
            "priority": c.priority.name,
            "disposition": c.disposition.name,
            "created_at": c.created_at,
            "title": c.title
        })
    return data

def journal_to_dataframe(entries: List[DecisionJournalEntry]) -> Any:
    data = []
    for e in entries:
        data.append({
            "case_id": e.case_id,
            "entry_type": e.entry_type,
            "actor": e.actor,
            "created_at": e.created_at,
            "note": e.note
        })
    return data

def data_actions_to_dataframe(actions: List[ReviewDataAction]) -> Any:
    data = []
    for a in actions:
        data.append({
            "action_id": a.action_id,
            "case_id": a.case_id,
            "status": a.status,
            "priority": a.priority.name,
            "description": a.description
        })
    return data

def format_review_case_text(case: ReviewCase) -> str:
    lines = [
        f"Case: {case.title} ({case.case_id})",
        f"Symbol: {case.symbol}",
        f"Status: {case.status.name}",
        f"Priority: {case.priority.name}",
        f"Disposition: {case.disposition.name}",
        f"Signoff Status: {case.signoff_status.name}",
        f"Conflicts: {', '.join(case.conflicts) if case.conflicts else 'None'}",
        f"Playbooks: {', '.join(case.playbook_ids) if case.playbook_ids else 'None'}",
        "\nDisclaimer: " + case.disclaimer
    ]
    return "\n".join(lines)

def format_checklist_text(items: List[ReviewChecklistItem]) -> str:
    lines = ["Checklist:"]
    for i in items:
        req = "*" if i.required else ""
        lines.append(f" - [{i.status.name}] {i.title}{req}")
    return "\n".join(lines)

def format_journal_text(entries: List[DecisionJournalEntry]) -> str:
    lines = ["Decision Journal:"]
    for e in sorted(entries, key=lambda x: x.created_at):
        actor = e.actor or "System"
        lines.append(f" - {e.created_at.strftime('%Y-%m-%d %H:%M:%S')} [{actor}] ({e.entry_type}): {e.note}")
    if entries:
        lines.append("\nDisclaimer: " + entries[0].disclaimer)
    return "\n".join(lines)

def format_signoff_text(signoff: ReviewSignoffRequest) -> str:
    lines = [
        f"Signoff: {signoff.signoff_id}",
        f"Status: {signoff.status.name}",
        f"Requested By: {signoff.requested_by or 'System'}",
        f"Reason: {signoff.reason}",
        f"Approved By: {signoff.approved_by if signoff.approved_by else 'N/A'}",
        "\nDisclaimer: " + signoff.disclaimer
    ]
    return "\n".join(lines)

def format_review_workflow_report_markdown(report: ReviewWorkflowReport) -> str:
    lines = [
        "# Review Workflow Report",
        f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"Total Cases: {len(report.cases)}",
        f"Total Journal Entries: {len(report.journal_entries)}",
        f"Pending Data Actions: {len([a for a in report.data_actions if a.status != 'RESOLVED'])}\n",
        "## Key Findings"
    ]
    for kf in report.key_findings:
        lines.append(f"- {kf}")

    lines.append("\n## Disclaimer")
    lines.append(report.disclaimer)

    return "\n".join(lines)
