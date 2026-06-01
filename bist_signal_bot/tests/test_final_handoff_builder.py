import pytest
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder

def test_final_handoff_builder_module_summaries():
    builder = FinalHandoffBuilder()
    summaries = builder.collect_module_summaries()
    assert len(summaries) > 0
    assert any(s.module_name == "config" for s in summaries)

def test_final_handoff_builder_latest_release_status():
    builder = FinalHandoffBuilder()
    status = builder.collect_latest_release_status()
    assert "release_candidate_id" in status

def test_final_handoff_builder_build():
    builder = FinalHandoffBuilder()
    manifest = builder.build_handoff()
    assert manifest.project_name == "BIST Signal Bot"
    assert manifest.final_status.value in ("PASS", "FAIL")
    assert len(manifest.module_summaries) > 0
    assert len(manifest.command_entries) > 0
