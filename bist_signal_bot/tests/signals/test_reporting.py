import pytest
import pandas as pd
from datetime import datetime, timezone

from bist_signal_bot.signals.models import (
    TrackedSignal,
    SignalLifecycleEvent,
    AlertEvaluationResult,
    WatchlistEntry,
    ResearchExitSimulation,
    SignalLifecycleSummary,
    SignalLifecycleState,
    SignalPriority,
    SignalOutcomeState,
    SignalLifecycleEventType,
    SignalAlertDecision,
    ResearchExitRuleType
)
from bist_signal_bot.signals.reporting import (
    tracked_signal_to_dict,
    lifecycle_event_to_dict,
    alert_evaluation_to_dict,
    watchlist_entry_to_dict,
    exit_simulation_to_dict,
    signals_to_dataframe,
    events_to_dataframe,
    watchlist_to_dataframe,
    format_tracked_signal_text,
    format_signal_lifecycle_summary,
    format_watchlist_text,
    format_exit_simulation_text,
    format_signal_report_markdown
)

@pytest.fixture
def mock_tracked_signal() -> TrackedSignal:
    return TrackedSignal(
        signal_id="sig-123",
        fingerprint_id="fp-123",
        symbol="THYAO",
        strategy_name="MACD_Crossover",
        source_type="SYSTEM",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        state=SignalLifecycleState.ACTIVE,
        priority=SignalPriority.HIGH,
        direction="LONG",
        current_score=85.5,
        watchlist=True,
        outcome_state=SignalOutcomeState.PENDING,
        disclaimer="Tracked signal is research-only. Not investment advice. No real order was sent."
    )

@pytest.fixture
def mock_lifecycle_event() -> SignalLifecycleEvent:
    return SignalLifecycleEvent(
        event_id="evt-123",
        signal_id="sig-123",
        event_type=SignalLifecycleEventType.CREATED,
        previous_state=None,
        new_state=SignalLifecycleState.NEW,
        timestamp=datetime.now(timezone.utc),
        message="Signal created"
    )

@pytest.fixture
def mock_alert_evaluation() -> AlertEvaluationResult:
    return AlertEvaluationResult(
        signal_id="sig-123",
        fingerprint_id="fp-123",
        decision=SignalAlertDecision.SEND,
        should_send=True,
        should_add_to_digest=True,
        reason="Score is high"
    )

@pytest.fixture
def mock_watchlist_entry() -> WatchlistEntry:
    return WatchlistEntry(
        watchlist_id="wl-123",
        signal_id="sig-123",
        symbol="THYAO",
        strategy_name="MACD_Crossover",
        added_at=datetime.now(timezone.utc),
        active=True
    )

@pytest.fixture
def mock_exit_simulation() -> ResearchExitSimulation:
    return ResearchExitSimulation(
        simulation_id="sim-123",
        signal_id="sig-123",
        symbol="THYAO",
        started_at=datetime.now(timezone.utc),
        evaluated_at=datetime.now(timezone.utc),
        entry_reference_price=100.0,
        current_price=110.0,
        triggered_rule=ResearchExitRuleType.FIXED_PERCENT_TARGET,
        outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET,
        simulated_return_pct=10.0
    )

@pytest.fixture
def mock_lifecycle_summary() -> SignalLifecycleSummary:
    return SignalLifecycleSummary(
        total_signals=100,
        active_count=20,
        watching_count=10,
        muted_count=5,
        expired_count=15,
        invalidated_count=10,
        completed_count=40,
        alerts_sent=50,
        alerts_muted=30,
        watchlist_count=15,
        generated_at=datetime.now(timezone.utc)
    )


def test_tracked_signal_to_dict(mock_tracked_signal):
    result = tracked_signal_to_dict(mock_tracked_signal)
    assert isinstance(result, dict)
    assert result['signal_id'] == 'sig-123'
    assert result['symbol'] == 'THYAO'
    assert 'metadata' not in result

def test_lifecycle_event_to_dict(mock_lifecycle_event):
    result = lifecycle_event_to_dict(mock_lifecycle_event)
    assert isinstance(result, dict)
    assert result['event_id'] == 'evt-123'
    assert result['event_type'] == 'CREATED'

def test_alert_evaluation_to_dict(mock_alert_evaluation):
    result = alert_evaluation_to_dict(mock_alert_evaluation)
    assert isinstance(result, dict)
    assert result['decision'] == 'SEND'
    assert result['should_send'] is True

def test_watchlist_entry_to_dict(mock_watchlist_entry):
    result = watchlist_entry_to_dict(mock_watchlist_entry)
    assert isinstance(result, dict)
    assert result['watchlist_id'] == 'wl-123'
    assert result['symbol'] == 'THYAO'

def test_exit_simulation_to_dict(mock_exit_simulation):
    result = exit_simulation_to_dict(mock_exit_simulation)
    assert isinstance(result, dict)
    assert result['simulation_id'] == 'sim-123'
    assert result['triggered_rule'] == 'FIXED_PERCENT_TARGET'

def test_signals_to_dataframe(mock_tracked_signal):
    # Test with valid list
    df = signals_to_dataframe([mock_tracked_signal])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['signal_id'] == 'sig-123'

    # Test empty list
    df_empty = signals_to_dataframe([])
    assert isinstance(df_empty, pd.DataFrame)
    assert len(df_empty) == 0

def test_events_to_dataframe(mock_lifecycle_event):
    # Test with valid list
    df = events_to_dataframe([mock_lifecycle_event])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['event_id'] == 'evt-123'

    # Test empty list
    df_empty = events_to_dataframe([])
    assert isinstance(df_empty, pd.DataFrame)
    assert len(df_empty) == 0

def test_watchlist_to_dataframe(mock_watchlist_entry):
    # Test with valid list
    df = watchlist_to_dataframe([mock_watchlist_entry])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['watchlist_id'] == 'wl-123'

    # Test empty list
    df_empty = watchlist_to_dataframe([])
    assert isinstance(df_empty, pd.DataFrame)
    assert len(df_empty) == 0


def test_format_tracked_signal_text(mock_tracked_signal):
    result = format_tracked_signal_text(mock_tracked_signal)
    assert isinstance(result, str)
    assert "Symbol: THYAO" in result
    assert "Strategy: MACD_Crossover" in result
    assert "State: ACTIVE" in result
    assert "Priority: HIGH" in result
    assert "Score: 85.5" in result
    assert "Watchlist: Yes" in result
    assert "Outcome: PENDING" in result
    assert "Disclaimer: Tracked signal is research-only." in result

def test_format_signal_lifecycle_summary(mock_lifecycle_summary):
    result = format_signal_lifecycle_summary(mock_lifecycle_summary)
    assert isinstance(result, str)
    assert "Total: 100" in result
    assert "Active: 20" in result
    assert "Alerts Sent: 50" in result
    assert "Watchlist: 15" in result
    assert "Not investment advice. No real orders sent." in result

def test_format_watchlist_text(mock_watchlist_entry):
    result = format_watchlist_text([mock_watchlist_entry])
    assert isinstance(result, str)
    assert "Watchlist Entries:" in result
    assert "- THYAO [MACD_Crossover] (Active: True)" in result
    assert "Watchlist is a research list, not a trading recommendation." in result

def test_format_exit_simulation_text(mock_exit_simulation):
    result = format_exit_simulation_text(mock_exit_simulation)
    assert isinstance(result, str)
    assert "Exit Simulation for THYAO" in result
    assert "Entry Reference: 100.0" in result
    assert "Current Price: 110.0" in result
    assert "Triggered Rule: FIXED_PERCENT_TARGET" in result
    assert "Outcome: HIT_RESEARCH_TARGET" in result
    assert "Return %: 10.0" in result
    assert "Disclaimer: Exit simulation is research-only." in result

def test_format_signal_report_markdown(mock_tracked_signal, mock_lifecycle_summary):
    result = format_signal_report_markdown([mock_tracked_signal], mock_lifecycle_summary)
    assert isinstance(result, str)
    assert "# Signal Lifecycle Report" in result
    assert "- **Active**: 20" in result
    assert "- **Watching**: 10" in result
    assert "- **THYAO** [MACD_Crossover]: ACTIVE (Score: 85.5)" in result
    assert "> **Disclaimer**: This is a research report." in result
