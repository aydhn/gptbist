from pathlib import Path
from typing import Optional
# Mock Settings import for now since we don't have access to the real config module here.
# Assuming Settings has standard attributes, we'll pass it optionally.
class DummySettings:
    pass
Settings = DummySettings

from bist_signal_bot.maintenance_automation.storage import MaintenanceAutomationStore
from bist_signal_bot.maintenance_automation.cadence import MaintenanceCadenceRegistry
from bist_signal_bot.maintenance_automation.planner import MaintenancePlanner
from bist_signal_bot.maintenance_automation.runner import MaintenanceRunner
from bist_signal_bot.maintenance_automation.checks import MaintenanceCheckRunner
from bist_signal_bot.maintenance_automation.cleanup import MaintenanceCleanupEngine
from bist_signal_bot.maintenance_automation.retention import RetentionPolicyRegistry
from bist_signal_bot.maintenance_automation.rotation import ArtifactRotationEngine
from bist_signal_bot.maintenance_automation.backup import BackupManifestBuilder
from bist_signal_bot.maintenance_automation.staleness import MaintenanceStalenessDetector
from bist_signal_bot.maintenance_automation.manifest import MaintenanceManifestBuilder

def _get_base_dir(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> Path:
    if base_dir:
        return base_dir
    # Try to resolve via settings if we had real ones, fallback to default
    import os
    default_base = Path(os.getcwd()) / "data" / "maintenance_automation"
    return default_base

def create_maintenance_automation_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceAutomationStore:
    return MaintenanceAutomationStore(_get_base_dir(settings, base_dir))

def create_maintenance_cadence_registry(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceCadenceRegistry:
    return MaintenanceCadenceRegistry()

def create_maintenance_planner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenancePlanner:
    registry = create_maintenance_cadence_registry(settings, base_dir)
    return MaintenancePlanner(registry=registry)

def create_maintenance_runner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceRunner:
    check_runner = create_maintenance_check_runner(settings, base_dir)
    cleanup_engine = create_maintenance_cleanup_engine(settings, base_dir)
    backup_builder = create_backup_manifest_builder(settings, base_dir)
    return MaintenanceRunner(
        check_runner=check_runner,
        cleanup_engine=cleanup_engine,
        backup_builder=backup_builder
    )

def create_maintenance_check_runner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceCheckRunner:
    return MaintenanceCheckRunner()

def create_maintenance_cleanup_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceCleanupEngine:
    return MaintenanceCleanupEngine(_get_base_dir(settings, base_dir).parent) # parent should be data/

def create_retention_policy_registry(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> RetentionPolicyRegistry:
    return RetentionPolicyRegistry()

def create_artifact_rotation_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ArtifactRotationEngine:
    return ArtifactRotationEngine(_get_base_dir(settings, base_dir).parent)

def create_backup_manifest_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> BackupManifestBuilder:
    return BackupManifestBuilder(_get_base_dir(settings, base_dir).parent.parent) # Project root

def create_maintenance_staleness_detector(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceStalenessDetector:
    return MaintenanceStalenessDetector(_get_base_dir(settings, base_dir).parent.parent)

def create_maintenance_manifest_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MaintenanceManifestBuilder:
    return MaintenanceManifestBuilder()
