import pytest
from bist_signal_bot.calibration.outcomes import OutcomeDatasetBuilder
from bist_signal_bot.calibration.models import OutcomeLabel

def test_assign_outcome_label_net():
    builder = OutcomeDatasetBuilder()
    builder.settings.CALIBRATION_USE_NET_RETURN_FOR_LABEL = True
    builder.settings.CALIBRATION_SUCCESS_RETURN_PCT = 1.0
    builder.settings.CALIBRATION_FAILURE_RETURN_PCT = -1.0

    assert builder.assign_outcome_label(5.0, 1.5) == OutcomeLabel.SUCCESS
    assert builder.assign_outcome_label(5.0, -1.5) == OutcomeLabel.FAILURE
    assert builder.assign_outcome_label(5.0, 0.5) == OutcomeLabel.PARTIAL_SUCCESS

def test_record_from_signal_outcome():
    builder = OutcomeDatasetBuilder()
    payload = {
        "signal_id": "s1",
        "symbol": "GARAN",
        "strategy_name": "test_strat",
        "gross_return_pct": 2.0,
        "net_return_pct": 1.5
    }
    record = builder.record_from_signal_outcome(payload)
    assert record.symbol == "GARAN"
    assert record.outcome_label == OutcomeLabel.SUCCESS
    assert record.net_return_pct == 1.5

def test_filter_evaluable():
    builder = OutcomeDatasetBuilder()
    records = [
        builder.record_from_signal_outcome({"gross_return_pct": 2.0, "net_return_pct": 1.5}),
        builder.record_from_signal_outcome({})
    ]
    evaluable = builder.filter_evaluable(records)
    assert len(evaluable) == 1
    assert evaluable[0].outcome_label == OutcomeLabel.SUCCESS
