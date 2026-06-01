import pytest
from bist_signal_bot.final_handoff.storage import FinalHandoffStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder

def test_final_handoff_store_manifest(tmp_path):
    settings = Settings()
    store = FinalHandoffStore(settings=settings, base_dir=tmp_path)
    builder = FinalHandoffBuilder(settings=settings)

    manifest = builder.build_handoff()
    store.append_manifest(manifest)

    loaded = store.load_latest_manifest()
    assert loaded is not None
    assert loaded.handoff_id == manifest.handoff_id

def test_final_handoff_store_command_map(tmp_path):
    settings = Settings()
    store = FinalHandoffStore(settings=settings, base_dir=tmp_path)
    builder = FinalCommandMapBuilder(settings=settings)

    entries = builder.build_command_map()
    store.save_command_map(entries)

    loaded = store.load_command_map()
    assert len(loaded) == len(entries)

def test_final_handoff_store_roadmap(tmp_path):
    settings = Settings()
    store = FinalHandoffStore(settings=settings, base_dir=tmp_path)
    builder = PostReleaseRoadmapBuilder(settings=settings)

    items = builder.build_roadmap()
    store.save_roadmap(items)

    loaded = store.load_roadmap()
    assert len(loaded) == len(items)

def test_reporting_markdown_disclaimer():
    from bist_signal_bot.final_handoff.models import OperatorPlaybook
    from bist_signal_bot.final_handoff.reporting import format_operator_playbook_markdown

    playbook = OperatorPlaybook(playbook_id="1", title="test")
    md = format_operator_playbook_markdown(playbook)
    assert "No real order was sent" in md
