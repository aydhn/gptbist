import pytest
from datetime import datetime
from bist_signal_bot.final_handoff.models import (
    FinalModuleSummary, FinalCommandMapEntry, OperatorPlaybook,
    DeveloperPlaybook, PostReleaseRoadmapItem, MaintenanceTask,
    FinalReleasePack, FinalHandoffManifest, FinalHandoffStatus,
    HandoffAudience, RoadmapPriority, MaintenanceCadence, ReleasePackStage
)

def test_final_module_summary_validation():
    summary = FinalModuleSummary(
        module_id="MOD_TEST",
        module_name="test_mod",
        title="Test Module",
        purpose="Test purpose",
        owner_area="System",
        status=FinalHandoffStatus.PASS
    )
    assert summary.module_id == "MOD_TEST"
    assert summary.status == FinalHandoffStatus.PASS

def test_final_command_map_entry_disclaimer():
    entry = FinalCommandMapEntry(
        entry_id="cmd_1",
        command="python -m test",
        category="test",
        audience=HandoffAudience.ALL,
        purpose="testing",
        safe_mode=True,
        dry_run_supported=True,
        json_supported=True
    )
    assert "not investment advice" in entry.disclaimer

def test_operator_playbook_routines():
    pb = OperatorPlaybook(
        playbook_id="pb_1",
        created_at=datetime.now(),
        title="Test PB",
        daily_routine=["task1"],
        weekly_routine=["task2"],
        monthly_routine=["task3"]
    )
    assert "task1" in pb.daily_routine

def test_developer_playbook_extension_points():
    pb = DeveloperPlaybook(
        playbook_id="pb_2",
        created_at=datetime.now(),
        title="Dev PB",
        extension_points=["ep1"]
    )
    assert "ep1" in pb.extension_points

def test_post_release_roadmap_item_priority():
    item = PostReleaseRoadmapItem(
        roadmap_id="rd_1",
        title="t",
        description="d",
        priority=RoadmapPriority.CRITICAL,
        target_area="core",
        status=FinalHandoffStatus.PASS
    )
    assert item.priority == RoadmapPriority.CRITICAL

def test_maintenance_task_cadence():
    task = MaintenanceTask(
        task_id="mt_1",
        title="t",
        cadence=MaintenanceCadence.WEEKLY,
        command_hint="cmd",
        owner_area="ops",
        expected_output="pass",
        requires_confirm=False
    )
    assert task.cadence == MaintenanceCadence.WEEKLY

def test_final_release_pack_disclaimer():
    pack = FinalReleasePack(
        pack_id="rp_1",
        created_at=datetime.now(),
        stage=ReleasePackStage.BUILT
    )
    assert "not investment advice" in pack.disclaimer

def test_final_handoff_manifest_known_limitations():
    manifest = FinalHandoffManifest(
        handoff_id="hm_1",
        created_at=datetime.now(),
        project_name="Test",
        project_summary="Test",
        final_status=FinalHandoffStatus.PASS,
        known_limitations=["limit1"]
    )
    assert "limit1" in manifest.known_limitations
