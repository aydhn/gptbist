import pytest
from bist_signal_bot.final_handoff.release_pack import FinalReleasePackBuilder
from bist_signal_bot.final_handoff.models import ReleasePackStage

def test_docs_hub_integration_docs_list():
    builder = FinalReleasePackBuilder()
    docs = builder.collect_docs()
    assert "docs/77_FINAL_MVP_HANDOFF.md" in docs

def test_bootstrap_release_bundle_pack_ref():
    # checking that pack can be built so bootstrap could reference it
    builder = FinalReleasePackBuilder()
    pack = builder.build_release_pack(stage=ReleasePackStage.BUILT)
    assert pack.stage == ReleasePackStage.BUILT

def test_cli_ux_command_registry_output_contract():
    # checking that command maps are created for CLI
    from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
    entries = FinalCommandMapBuilder().build_command_map()
    assert any(e.category == "final-handoff" for e in entries)
