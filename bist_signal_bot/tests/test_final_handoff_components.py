import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.operator_playbook import OperatorPlaybookBuilder
from bist_signal_bot.final_handoff.developer_playbook import DeveloperPlaybookBuilder
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.module_map import FinalModuleMapBuilder
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder
from bist_signal_bot.final_handoff.release_pack import FinalReleasePackBuilder
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder
from bist_signal_bot.final_handoff.models import HandoffAudience

def test_operator_playbook_builder_markdown():
    settings = Settings()
    builder = OperatorPlaybookBuilder(settings=settings)
    playbook = builder.build_playbook()
    md = builder.render_markdown(playbook)
    assert playbook.title in md
    assert "Daily Routine" in md
    assert "Weekly Routine" in md

def test_developer_playbook_builder_markdown():
    settings = Settings()
    builder = DeveloperPlaybookBuilder(settings=settings)
    playbook = builder.build_playbook()
    md = builder.render_markdown(playbook)
    assert playbook.title in md
    assert "Extension Points" in md

def test_command_map_builder_entries():
    settings = Settings()
    builder = FinalCommandMapBuilder(settings=settings)
    entries = builder.core_command_entries()
    assert len(entries) > 0

def test_command_map_builder_audience_filter():
    settings = Settings()
    builder = FinalCommandMapBuilder(settings=settings)
    entries = builder.core_command_entries()
    op_entries = builder.filter_by_audience(entries, HandoffAudience.OPERATOR)
    for e in op_entries:
        assert e.audience in [HandoffAudience.OPERATOR, HandoffAudience.ALL]

def test_module_map_builder_dependencies():
    settings = Settings()
    builder = FinalModuleMapBuilder(settings=settings)
    deps = builder.module_dependencies("final_handoff")
    assert "final_audit" in deps

def test_roadmap_builder_items():
    settings = Settings()
    builder = PostReleaseRoadmapBuilder(settings=settings)
    items = builder.build_roadmap()
    assert len(items) > 0
    phases = [item.suggested_phase for item in items]
    assert "101" in phases

def test_release_pack_builder(tmp_path):
    settings = Settings()
    builder = FinalReleasePackBuilder(settings=settings, base_dir=tmp_path)

    # Mock some files
    (tmp_path / "bist_signal_bot" / "docs").mkdir(parents=True)
    (tmp_path / "bist_signal_bot" / "docs" / "test.md").write_text("test")

    pack = builder.build_release_pack()
    assert len(pack.included_docs) > 0
    assert len(pack.checksum_manifest) > 0

def test_maintenance_cadence_builder():
    settings = Settings()
    builder = MaintenanceCadenceBuilder(settings=settings)
    tasks = builder.build_tasks()
    assert len(tasks) > 0
