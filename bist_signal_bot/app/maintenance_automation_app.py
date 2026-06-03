from pathlib import Path
from bist_signal_bot.config.settings import Settings
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

def create_maintenance_automation_store(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceAutomationStore: return MaintenanceAutomationStore()
def create_maintenance_cadence_registry(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceCadenceRegistry: return MaintenanceCadenceRegistry()
def create_maintenance_planner(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenancePlanner: return MaintenancePlanner()
def create_maintenance_runner(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceRunner: return MaintenanceRunner()
def create_maintenance_check_runner(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceCheckRunner: return MaintenanceCheckRunner()
def create_maintenance_cleanup_engine(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceCleanupEngine: return MaintenanceCleanupEngine()
def create_retention_policy_registry(settings: Settings | None = None, base_dir: Path | None = None) -> RetentionPolicyRegistry: return RetentionPolicyRegistry()
def create_artifact_rotation_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ArtifactRotationEngine: return ArtifactRotationEngine()
def create_backup_manifest_builder(settings: Settings | None = None, base_dir: Path | None = None) -> BackupManifestBuilder: return BackupManifestBuilder()
def create_maintenance_staleness_detector(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceStalenessDetector: return MaintenanceStalenessDetector()
def create_maintenance_manifest_builder(settings: Settings | None = None, base_dir: Path | None = None) -> MaintenanceManifestBuilder: return MaintenanceManifestBuilder()
