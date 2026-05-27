import pandas as pd
from typing import Any

from bist_signal_bot.events.models import (
    MarketEvent, EventWindow, EventRiskAssessment, BlackoutPolicy, EventImportResult, EventCalendarSnapshot, EventLink
)

def event_to_dict(event: MarketEvent) -> dict[str, Any]:
    return event.model_dump(mode='json')

def window_to_dict(window: EventWindow) -> dict[str, Any]:
    return window.model_dump(mode='json')

def assessment_to_dict(assessment: EventRiskAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode='json')

def policy_to_dict(policy: BlackoutPolicy) -> dict[str, Any]:
    return policy.model_dump(mode='json')

def import_result_to_dict(result: EventImportResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def snapshot_to_dict(snapshot: EventCalendarSnapshot) -> dict[str, Any]:
    return snapshot.model_dump(mode='json')

def event_link_to_dict(link: EventLink) -> dict[str, Any]:
    return link.model_dump(mode='json')

def events_to_dataframe(events: list[MarketEvent]) -> pd.DataFrame:
    data = [event_to_dict(e) for e in events]
    return pd.DataFrame(data)

def assessments_to_dataframe(assessments: list[EventRiskAssessment]) -> pd.DataFrame:
    data = [assessment_to_dict(a) for a in assessments]
    return pd.DataFrame(data)

def format_event_text(event: MarketEvent) -> str:
    return f"{event.event_date.strftime('%Y-%m-%d')} | {event.event_type.value} | {event.title} | {event.severity.value}"

def format_assessment_text(assessment: EventRiskAssessment) -> str:
    return f"{assessment.symbol} | Score: {assessment.risk_score} | Decision: {assessment.decision.value}"

def format_window_text(window: EventWindow) -> str:
    return f"{window.starts_at.strftime('%Y-%m-%d')} to {window.ends_at.strftime('%Y-%m-%d')} | {window.window_type.value} | {window.decision.value}"

def format_calendar_snapshot_text(snapshot: EventCalendarSnapshot) -> str:
    return f"Events: {snapshot.events_count} | Upcoming: {snapshot.upcoming_count} | High Severity: {snapshot.high_severity_count}"

def format_event_calendar_report_markdown(snapshot: EventCalendarSnapshot, upcoming: list[MarketEvent], assessments: list[EventRiskAssessment] | None = None) -> str:
    md = f"# Event Calendar Report\n\n"
    md += f"**Date**: {snapshot.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"**Disclaimer**: {snapshot.disclaimer}\n\n"

    md += "## Snapshot\n"
    md += f"- Total Events: {snapshot.events_count}\n"
    md += f"- Upcoming Events: {snapshot.upcoming_count}\n"
    md += f"- High Severity Events: {snapshot.high_severity_count}\n\n"

    md += "## Upcoming Events\n"
    for ev in upcoming:
        md += f"- {format_event_text(ev)}\n"

    if assessments:
        md += "\n## Risk Assessments\n"
        for ass in assessments:
            md += f"- {format_assessment_text(ass)}\n"

    return md
