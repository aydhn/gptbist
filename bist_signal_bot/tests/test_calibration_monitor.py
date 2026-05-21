import pytest
from bist_signal_bot.drift.calibration import CalibrationMonitor
from bist_signal_bot.drift.models import DriftStatus
from bist_signal_bot.config.settings import Settings

def test_calibration_insufficient():
    cm = CalibrationMonitor(Settings())
    res = cm.build_calibration_report([], [])
    assert res.status == DriftStatus.INSUFFICIENT_DATA

def test_calibration_perfect():
    cm = CalibrationMonitor(Settings())
    preds = [0.1, 0.5, 0.9]
    outs = [0, 1, 1]  # Brier won't be perfect, but let's check basic flow
    res = cm.build_calibration_report(preds, outs)
    # The counts are tiny but the ECE won't trigger fail threshold typically
    assert res.status != DriftStatus.INSUFFICIENT_DATA
    assert res.expected_calibration_error is not None
