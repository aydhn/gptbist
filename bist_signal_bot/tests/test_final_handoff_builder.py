import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder
from bist_signal_bot.final_handoff.models import FinalHandoffStatus

def test_final_handoff_builder_module_summaries():
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    builder = FinalHandoffBuilder(settings=settings)
    summaries = builder.collect_module_summaries()
    assert len(summaries) > 0

def test_final_handoff_builder_latest_release_status():
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    builder = FinalHandoffBuilder(settings=settings)
    status = builder.collect_latest_release_status()
    assert "release_candidate_id" in status
    assert "go_no_go_decision" in status

def test_final_handoff_builder_build_handoff():
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    builder = FinalHandoffBuilder(settings=settings)
    manifest = builder.build_handoff()

    assert manifest.project_name == "BIST Signal Bot"
    assert manifest.final_status in [FinalHandoffStatus.PASS, FinalHandoffStatus.WATCH, FinalHandoffStatus.FAIL, FinalHandoffStatus.UNKNOWN]
    assert len(manifest.module_summaries) > 0
    assert len(manifest.command_entries) > 0
    assert len(manifest.known_limitations) > 0
