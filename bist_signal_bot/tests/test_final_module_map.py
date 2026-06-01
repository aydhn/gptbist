import pytest
from bist_signal_bot.final_handoff.module_map import FinalModuleMapBuilder

def test_module_map_builder_dependencies():
    builder = FinalModuleMapBuilder()
    deps = builder.module_dependencies("final_handoff")
    assert "core" in deps
