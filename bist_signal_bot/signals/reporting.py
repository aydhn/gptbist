from typing import Any, Dict, List
import pandas as pd
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalLifecycleEvent, AlertEvaluationResult,
    WatchlistEntry, ResearchExitSimulation, SignalLifecycleSummary
)

def tracked_signal_to_dict(signal: TrackedSignal) -> Dict[str, Any]:
    return signal.safe_public_dict()

def lifecycle_event_to_dict(event: SignalLifecycleEvent) -> Dict[str, Any]:
    return event.model_dump(mode='json')

def alert_evaluation_to_dict(result: AlertEvaluationResult) -> Dict[str, Any]:
    return result.model_dump(mode='json')

def watchlist_entry_to_dict(entry: WatchlistEntry) -> Dict[str, Any]:
    return entry.model_dump(mode='json')

def exit_simulation_to_dict(simulation: ResearchExitSimulation) -> Dict[str, Any]:
    return simulation.model_dump(mode='json')

def signals_to_dataframe(signals: List[TrackedSignal]) -> pd.DataFrame:
    data = [tracked_signal_to_dict(s) for s in signals]
    return pd.DataFrame(data)

def events_to_dataframe(events: List[SignalLifecycleEvent]) -> pd.DataFrame:
    data = [lifecycle_event_to_dict(e) for e in events]
    return pd.DataFrame(data)

def watchlist_to_dataframe(entries: List[WatchlistEntry]) -> pd.DataFrame:
    data = [watchlist_entry_to_dict(e) for e in entries]
    return pd.DataFrame(data)

def format_tracked_signal_text(signal: TrackedSignal) -> str:
    lines = [
        f"Symbol: {signal.symbol}",
        f"Strategy: {signal.strategy_name or 'N/A'}",
        f"State: {signal.state.value}",
        f"Priority: {signal.priority.value}",
        f"Score: {signal.current_score}",
        f"Watchlist: {'Yes' if signal.watchlist else 'No'}",
        f"Outcome: {signal.outcome_state.value}",
        f"\nDisclaimer: {signal.disclaimer}"
    ]
    return "\n".join(lines)

def format_signal_lifecycle_summary(summary: SignalLifecycleSummary) -> str:
    lines = [
        "BIST Bot Signal Lifecycle Summary",
        f"Total: {summary.total_signals}",
        f"Active: {summary.active_count}",
        f"Watching: {summary.watching_count}",
        f"Muted: {summary.muted_count}",
        f"Expired: {summary.expired_count}",
        f"Invalidated: {summary.invalidated_count}",
        f"Completed: {summary.completed_count}",
        f"Alerts Sent: {summary.alerts_sent}",
        f"Alerts Muted: {summary.alerts_muted}",
        f"Watchlist: {summary.watchlist_count}",
        "\nThis output is a research summary. Not investment advice. No real orders sent."
    ]
    return "\n".join(lines)

def format_watchlist_text(entries: List[WatchlistEntry]) -> str:
    lines = ["Watchlist Entries:"]
    for e in entries:
        lines.append(f"- {e.symbol} [{e.strategy_name}] (Active: {e.active})")
    lines.append("\nWatchlist is a research list, not a trading recommendation.")
    return "\n".join(lines)

def format_exit_simulation_text(simulation: ResearchExitSimulation) -> str:
    lines = [
        f"Exit Simulation for {simulation.symbol}",
        f"Entry Reference: {simulation.entry_reference_price}",
        f"Current Price: {simulation.current_price}",
        f"Triggered Rule: {simulation.triggered_rule.value}",
        f"Outcome: {simulation.outcome_state.value}",
        f"Return %: {simulation.simulated_return_pct}",
        f"\nDisclaimer: {simulation.disclaimer}"
    ]
    return "\n".join(lines)

def format_signal_report_markdown(signals: List[TrackedSignal], summary: SignalLifecycleSummary) -> str:
    # A simple markdown summary
    md = f"# Signal Lifecycle Report\n\n"
    md += f"## Summary\n"
    md += f"- **Active**: {summary.active_count}\n"
    md += f"- **Watching**: {summary.watching_count}\n"
    md += f"- **Alerts Muted**: {summary.alerts_muted}\n"
    md += f"- **Watchlist**: {summary.watchlist_count}\n\n"
    md += f"## Recent Signals\n"

    for s in signals[:10]: # show top 10 recent
        md += f"- **{s.symbol}** [{s.strategy_name}]: {s.state.value} (Score: {s.current_score})\n"

    md += "\n> **Disclaimer**: This is a research report. Not investment advice. No real order sent."
    return md
