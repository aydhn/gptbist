import pytest
from bist_signal_bot.final_handoff.models import (
    FinalModuleSummary, FinalHandoffStatus, FinalCommandMapEntry, HandoffAudience,
    OperatorPlaybook, DeveloperPlaybook, PostReleaseRoadmapItem, RoadmapPriority,
    MaintenanceTask, MaintenanceCadence, FinalReleasePack, ReleasePackStage,
    FinalHandoffManifest, FinalHandoffReport
)

def test_final_module_summary_validation():
    summary = FinalModuleSummary(
        module_id="123",
        module_name="test_mod",
        title="Test Mod",
        purpose="Test purpose",
        owner_area="test",
        status=FinalHandoffStatus.PASS
    )
    assert summary.status == FinalHandoffStatus.PASS

def test_final_command_map_entry_disclaimer():
    entry = FinalCommandMapEntry(
        entry_id="456",
        command="test",
        category="test",
        audience=HandoffAudience.USER,
        purpose="testing"
    )
    assert "not investment advice" in entry.disclaimer
    assert "No real order was sent" in entry.disclaimer

def test_operator_playbook_routines():
    playbook = OperatorPlaybook(
        playbook_id="789",
        title="Ops",
        daily_routine=["cmd1"],
        weekly_routine=["cmd2"],
        monthly_routine=["cmd3"]
    )
    assert len(playbook.daily_routine) == 1
    assert len(playbook.weekly_routine) == 1
    assert len(playbook.monthly_routine) == 1

def test_developer_playbook_extension_points():
    playbook = DeveloperPlaybook(
        playbook_id="000",
        title="Dev",
        extension_points=["ext1"]
    )
    assert len(playbook.extension_points) == 1

def test_post_release_roadmap_item_priority():
    item = PostReleaseRoadmapItem(
        roadmap_id="111",
        title="Item",
        description="Desc",
        priority=RoadmapPriority.HIGH,
        target_area="core",
        status=FinalHandoffStatus.PASS
    )
    assert item.priority == RoadmapPriority.HIGH

def test_maintenance_task_cadence():
    task = MaintenanceTask(
        task_id="222",
        title="Task",
        cadence=MaintenanceCadence.WEEKLY,
        command_hint="cmd",
        owner_area="ops",
        expected_output="ok"
    )
    assert task.cadence == MaintenanceCadence.WEEKLY

def test_final_release_pack_disclaimer():
    pack = FinalReleasePack(
        pack_id="333",
        stage=ReleasePackStage.BUILT
    )
    assert "No real order was sent" in pack.disclaimer

def test_final_handoff_manifest_known_limitations():
    manifest = FinalHandoffManifest(
        handoff_id="444",
        project_name="Test",
        project_summary="Test sum",
        final_status=FinalHandoffStatus.PASS,
        known_limitations=["limit1"]
    )
    assert len(manifest.known_limitations) == 1
