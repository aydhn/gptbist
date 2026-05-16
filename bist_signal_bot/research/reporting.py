import pandas as pd
from typing import Any

from .models import (
    ResearchRun, ResearchLedgerEntry, SignalJournalEntry,
    ResearchComparisonReport, AttributionReport, ResearchComparisonItem, AttributionBucket
)

def research_run_to_dict(run: ResearchRun) -> dict[str, Any]:
    return run.safe_public_dict()

def ledger_entries_to_dataframe(entries: list[ResearchLedgerEntry]) -> pd.DataFrame:
    data = []
    for e in entries:
        r = e.run
        data.append({
            "entry_id": e.entry_id,
            "run_id": r.run_id,
            "run_type": r.run_type.value,
            "status": r.status.value,
            "timestamp": e.timestamp,
            "title": r.title,
            "strategy": r.strategy_name,
            "symbol_count": len(r.symbols),
            "message": e.message
        })
    return pd.DataFrame(data)

def journal_entries_to_dataframe(entries: list[SignalJournalEntry]) -> pd.DataFrame:
    data = []
    for e in entries:
        data.append({
            "journal_id": e.journal_id,
            "timestamp": e.timestamp,
            "symbol": e.symbol,
            "strategy": e.strategy_name,
            "direction": e.direction,
            "outcome": e.outcome.value,
            "outcome_return_pct": e.outcome_return_pct,
            "score": e.signal_score
        })
    return pd.DataFrame(data)

def comparison_report_to_dict(report: ResearchComparisonReport) -> dict[str, Any]:
    return report.model_dump()

def attribution_report_to_dict(report: AttributionReport) -> dict[str, Any]:
    return report.model_dump()

def comparison_items_to_dataframe(items: list[ResearchComparisonItem]) -> pd.DataFrame:
    data = []
    for i in items:
        row = {"run_id": i.run_id, "label": i.label, "rank": i.rank, "score": i.score}
        row.update(i.metrics)
        data.append(row)
    return pd.DataFrame(data)

def attribution_buckets_to_dataframe(buckets: list[AttributionBucket]) -> pd.DataFrame:
    data = []
    for b in buckets:
        data.append({
            "group": b.group_key,
            "count": b.count,
            "win_rate": b.win_rate,
            "avg_return": b.average_return_pct,
            "total_pnl": b.total_pnl,
            "avg_score": b.average_score
        })
    return pd.DataFrame(data)

def format_research_run_text(run: ResearchRun) -> str:
    lines = [
        f"--- RESEARCH RUN: {run.title} ---",
        f"ID: {run.run_id} | Type: {run.run_type.value} | Status: {run.status.value}",
        f"Strategy: {run.strategy_name} | Symbols: {len(run.symbols)}",
        f"Time: {run.started_at} -> {run.finished_at}",
        f"Elapsed: {run.elapsed_seconds:.2f}s" if run.elapsed_seconds else "Elapsed: N/A",
        f"Disclaimer: {run.disclaimer}",
        "\nMetrics:"
    ]
    for k, v in run.metrics.items():
        if isinstance(v, float):
             lines.append(f"  {k}: {v:.4f}")
        else:
             lines.append(f"  {k}: {v}")
    return "\n".join(lines)

def format_ledger_summary_text(entries: list[ResearchLedgerEntry]) -> str:
    if not entries: return "No ledger entries."
    lines = ["--- RESEARCH LEDGER SUMMARY ---"]
    for e in entries:
        r = e.run
        lines.append(f"{e.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {r.run_type.value:<15} | {r.status.value:<10} | {r.run_id} | {r.title}")
    return "\n".join(lines)

def format_signal_journal_text(entries: list[SignalJournalEntry]) -> str:
    if not entries: return "No journal entries."
    lines = ["--- SIGNAL JOURNAL ---"]
    for e in entries:
        lines.append(f"{e.timestamp.strftime('%Y-%m-%d %H:%M')} | {e.symbol:<6} | {e.strategy_name:<20} | {str(e.direction):<5} | Out: {e.outcome.value}")
    return "\n".join(lines)

def format_comparison_report_text(report: ResearchComparisonReport) -> str:
    lines = [
        f"--- RESEARCH COMPARISON: {report.title} ---",
        f"Metric: {report.sort_metric}",
        f"Disclaimer: {report.disclaimer}",
        "\nRankings:"
    ]
    for item in report.items:
        lines.append(f"{item.rank}. {item.label} (Score: {item.score}) [Run: {item.run_id}]")
    if report.findings:
        lines.append("\nFindings:")
        for f in report.findings:
            lines.append(f" - {f}")
    return "\n".join(lines)

def format_attribution_report_text(report: AttributionReport) -> str:
    lines = [
        f"--- ATTRIBUTION REPORT by {report.group_by.value} ---",
        f"Disclaimer: {report.disclaimer}",
        "\nBuckets:"
    ]
    for b in report.buckets:
        wr = f"{b.win_rate:.1f}%" if b.win_rate is not None else "N/A"
        ar = f"{b.average_return_pct:.2f}%" if b.average_return_pct is not None else "N/A"
        lines.append(f"[{b.group_key}] Count: {b.count} | WinRate: {wr} | AvgReturn: {ar}")
    if report.findings:
        lines.append("\nFindings:")
        for f in report.findings:
            lines.append(f" - {f}")
    return "\n".join(lines)

def format_research_report_markdown(run_or_report: Any) -> str:
    if isinstance(run_or_report, ResearchRun):
        r = run_or_report
        return f"""# Research Run: {r.title}
**ID:** {r.run_id}
**Type:** {r.run_type.value}
**Status:** {r.status.value}

> {r.disclaimer}

## Details
- **Strategy:** {r.strategy_name}
- **Symbols:** {len(r.symbols)}
- **Started At:** {r.started_at}

## Metrics
```json
{r.metrics}
```
"""
    elif isinstance(run_or_report, ResearchComparisonReport):
        return f"# Comparison Report: {run_or_report.title}\n\n> {run_or_report.disclaimer}\n\n" + "\n".join(f"- {i.rank}. {i.label}: {i.score}" for i in run_or_report.items)
    elif isinstance(run_or_report, AttributionReport):
        return f"# Attribution Report: {run_or_report.group_by.value}\n\n> {run_or_report.disclaimer}\n\n" + "\n".join(f"- {b.group_key}: {b.count} signals, WinRate: {b.win_rate}%" for b in run_or_report.buckets)
    return str(run_or_report)
