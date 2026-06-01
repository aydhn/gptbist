import pytest
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.models import HandoffAudience

def test_command_map_builder_entries():
    builder = FinalCommandMapBuilder()
    entries = builder.build_command_map()
    assert len(entries) > 0
    assert any("final-handoff" in e.command for e in entries)

def test_command_map_builder_audience_filter():
    builder = FinalCommandMapBuilder()
    entries = builder.build_command_map()
    filtered = builder.filter_by_audience(entries, HandoffAudience.DEVELOPER)
    assert all(e.audience in (HandoffAudience.DEVELOPER, HandoffAudience.ALL) for e in filtered)
