import pytest
from bist_signal_bot.final_handoff.storage import FinalHandoffStore
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder

def test_final_handoff_storage_manifest(tmp_path):
    store = FinalHandoffStore(base_dir=tmp_path)
    builder = FinalHandoffBuilder()
    manifest = builder.build_handoff()
    store.append_manifest(manifest)

    loaded = store.load_latest_manifest()
    assert loaded is not None
    assert loaded.handoff_id == manifest.handoff_id

def test_final_handoff_storage_command_map(tmp_path):
    store = FinalHandoffStore(base_dir=tmp_path)
    from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
    entries = FinalCommandMapBuilder().build_command_map()

    store.save_command_map(entries)
    loaded = store.load_command_map()
    assert len(loaded) > 0
    assert loaded[0].command == entries[0].command

def test_final_handoff_storage_roadmap(tmp_path):
    store = FinalHandoffStore(base_dir=tmp_path)
    from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder
    items = PostReleaseRoadmapBuilder().build_roadmap()

    store.save_roadmap(items)
    loaded = store.load_roadmap()
    assert len(loaded) > 0
    assert loaded[0].title == items[0].title
