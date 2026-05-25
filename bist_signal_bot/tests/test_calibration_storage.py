import pytest
from pathlib import Path
from bist_signal_bot.calibration.storage import CalibrationStore
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationResult, CalibrationScoreType, OutcomeHorizon
from bist_signal_bot.config.settings import Settings
from datetime import datetime, UTC

def test_storage_append_load(tmp_path):
    settings = Settings()
    store = CalibrationStore(settings, base_dir=tmp_path)

    records = [OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC))]
    store.append_outcomes(records)

    loaded = store.load_outcomes()
    assert len(loaded) == 1
    assert loaded[0].outcome_id == "1"
