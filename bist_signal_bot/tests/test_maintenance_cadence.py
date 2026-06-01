import pytest
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder
from bist_signal_bot.final_handoff.models import MaintenanceCadence

def test_maintenance_cadence_builder_tasks():
    builder = MaintenanceCadenceBuilder()
    tasks = builder.build_tasks()
    assert len(tasks) > 0
    assert any(t.cadence == MaintenanceCadence.DAILY for t in tasks)
    assert any(t.cadence == MaintenanceCadence.WEEKLY for t in tasks)
