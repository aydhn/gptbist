import pytest
from bist_signal_bot.signals.outcomes import SignalOutcomeTracker
from bist_signal_bot.signals.models import TrackedSignal, SignalOutcomeState, ResearchExitSimulation, ResearchExitRuleType, SignalLifecycleState
from bist_signal_bot.signals.storage import SignalStore
from datetime import datetime, timezone

from unittest.mock import patch
@pytest.fixture
def store(tmp_path):
    return SignalStore(tmp_path)

@pytest.fixture
def tracker(store):
    return SignalOutcomeTracker(store)

def test_update_from_exit_simulation_success(tracker, store):
    now = datetime.now(timezone.utc)
    s = TrackedSignal(signal_id="sig1", fingerprint_id="fp1", symbol="ASELS", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s)

    sim = ResearchExitSimulation(
        simulation_id="sim1",
        signal_id="sig1",
        symbol="ASELS",
        started_at=now,
        evaluated_at=now,
        triggered_rule=ResearchExitRuleType.FIXED_PERCENT_TARGET,
        outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET,
        simulated_return_pct=5.0
    )

    updated = tracker.update_from_exit_simulation(sim)
    assert updated.outcome_state == SignalOutcomeState.HIT_RESEARCH_TARGET
    assert updated.outcome_return_pct == 5.0

def test_update_from_exit_simulation_not_found(tracker):
    now = datetime.now(timezone.utc)
    sim = ResearchExitSimulation(
        simulation_id="sim1",
        signal_id="missing_sig",
        symbol="ASELS",
        started_at=now,
        evaluated_at=now,
        triggered_rule=ResearchExitRuleType.FIXED_PERCENT_TARGET,
        outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET,
        simulated_return_pct=5.0
    )
    with pytest.raises(ValueError, match="Signal not found: missing_sig"):
        tracker.update_from_exit_simulation(sim)


@patch("bist_signal_bot.signals.outcomes.get_settings")
def test_update_manual_outcome_requires_confirm(mock_get_settings, tracker, store):
    mock_settings = mock_get_settings.return_value
    mock_settings.SIGNAL_EXIT_REQUIRE_CONFIRM_FOR_MANUAL_OUTCOME = True
    tracker.settings = mock_settings

    now = datetime.now(timezone.utc)
    s = TrackedSignal(signal_id="sig1", fingerprint_id="fp1", symbol="ASELS", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s)
    with pytest.raises(ValueError, match="Confirm flag required for manual outcome update"):
        tracker.update_manual_outcome("sig1", SignalOutcomeState.MANUAL_CLOSED, 2.0, confirm=False)

def test_update_manual_outcome_not_found(tracker):
    with pytest.raises(ValueError, match="Signal not found: missing_sig"):
        tracker.update_manual_outcome("missing_sig", SignalOutcomeState.MANUAL_CLOSED, 2.0, confirm=True)

def test_sync_to_research_journal(tracker, store):
    now = datetime.now(timezone.utc)
    s = TrackedSignal(
        signal_id="sig1",
        fingerprint_id="fp1",
        symbol="ASELS",
        source_type="TEST",
        created_at=now,
        updated_at=now,
        outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET,
        outcome_return_pct=10.5,
        state=SignalLifecycleState.COMPLETED
    )
    journal = tracker.sync_to_research_journal(s)
    assert journal["signal_id"] == "sig1"
    assert journal["fingerprint_id"] == "fp1"
    assert journal["symbol"] == "ASELS"
    assert journal["outcome_state"] == SignalOutcomeState.HIT_RESEARCH_TARGET.value
    assert journal["return_pct"] == 10.5
    assert journal["lifecycle_state"] == SignalLifecycleState.COMPLETED.value

def test_summarize_outcomes(tracker, store):
    now = datetime.now(timezone.utc)
    signals = [
        TrackedSignal(signal_id="s1", fingerprint_id="fp1", symbol="ASELS", strategy_name="S1", source_type="TEST", created_at=now, updated_at=now, outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET, outcome_return_pct=10.0),
        TrackedSignal(signal_id="s2", fingerprint_id="fp2", symbol="ASELS", strategy_name="S1", source_type="TEST", created_at=now, updated_at=now, outcome_state=SignalOutcomeState.HIT_RESEARCH_STOP, outcome_return_pct=-5.0),
        TrackedSignal(signal_id="s3", fingerprint_id="fp3", symbol="THYAO", strategy_name="S2", source_type="TEST", created_at=now, updated_at=now, outcome_state=SignalOutcomeState.TIME_EXPIRED, outcome_return_pct=1.0),
        TrackedSignal(signal_id="s4", fingerprint_id="fp4", symbol="THYAO", strategy_name="S2", source_type="TEST", created_at=now, updated_at=now, outcome_state=SignalOutcomeState.INVALIDATED_BY_RISK, outcome_return_pct=0.0)
    ]
    for s in signals:
        store.append_signal(s)

    # Test total summary
    summary = tracker.summarize_outcomes()
    assert summary["target_hits"] == 1
    assert summary["stop_hits"] == 1
    assert summary["time_expired"] == 1
    assert summary["invalidated"] == 1
    assert summary["tracked_count"] == 4
    assert summary["average_simulated_return"] == 1.5

    # Test filtering by symbol
    summary_asels = tracker.summarize_outcomes(symbol="ASELS")
    assert summary_asels["target_hits"] == 1
    assert summary_asels["stop_hits"] == 1
    assert summary_asels["tracked_count"] == 2
    assert summary_asels["average_simulated_return"] == 2.5

    # Test filtering by strategy
    summary_s2 = tracker.summarize_outcomes(strategy_name="S2")
    assert summary_s2["time_expired"] == 1
    assert summary_s2["invalidated"] == 1
    assert summary_s2["tracked_count"] == 2
    assert summary_s2["average_simulated_return"] == 0.5

def test_update_manual_outcome_success(tracker, store):
    now = datetime.now(timezone.utc)
    s = TrackedSignal(signal_id="sig2", fingerprint_id="fp2", symbol="THYAO", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s)

    updated = tracker.update_manual_outcome("sig2", SignalOutcomeState.MANUAL_CLOSED, 2.5, confirm=True)
    assert updated.outcome_state == SignalOutcomeState.MANUAL_CLOSED
    assert updated.outcome_return_pct == 2.5

    s_updated = store.get_signal("sig2")
    assert s_updated.outcome_state == SignalOutcomeState.MANUAL_CLOSED
