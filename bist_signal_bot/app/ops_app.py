from pathlib import Path
from bist_signal_bot.config.settings import Settings

from bist_signal_bot.ops.storage import OpsStore
from bist_signal_bot.ops.observability import OpsObservabilityEngine
from bist_signal_bot.ops.store_checks import StoreIntegrityChecker
from bist_signal_bot.ops.staleness import StalenessChecker
from bist_signal_bot.ops.incidents import OpsIncidentManager
from bist_signal_bot.ops.runbooks import OpsRunbookRegistry
from bist_signal_bot.ops.backup import BackupManager
from bist_signal_bot.ops.restore import RestorePlanner
from bist_signal_bot.ops.retention import RetentionPolicyEngine
from bist_signal_bot.ops.migrations import MigrationChecker
from bist_signal_bot.ops.readiness import OperationalReadinessGate

def create_ops_store(settings: Settings | None = None, base_dir: Path | None = None) -> OpsStore:
    return OpsStore(settings=settings, base_dir=base_dir)

def create_ops_observability_engine(settings: Settings | None = None, base_dir: Path | None = None) -> OpsObservabilityEngine:
    return OpsObservabilityEngine(settings=settings, base_dir=base_dir)

def create_store_integrity_checker(settings: Settings | None = None, base_dir: Path | None = None) -> StoreIntegrityChecker:
    return StoreIntegrityChecker(settings=settings, base_dir=base_dir)

def create_staleness_checker(settings: Settings | None = None, base_dir: Path | None = None) -> StalenessChecker:
    return StalenessChecker(settings=settings, base_dir=base_dir)

def create_ops_incident_manager(settings: Settings | None = None, base_dir: Path | None = None) -> OpsIncidentManager:
    store = create_ops_store(settings, base_dir)
    return OpsIncidentManager(settings=settings, base_dir=base_dir, store=store)

def create_ops_runbook_registry(settings: Settings | None = None, base_dir: Path | None = None) -> OpsRunbookRegistry:
    store = create_ops_store(settings, base_dir)
    return OpsRunbookRegistry(settings=settings, base_dir=base_dir, store=store)

def create_backup_manager(settings: Settings | None = None, base_dir: Path | None = None) -> BackupManager:
    store = create_ops_store(settings, base_dir)
    return BackupManager(settings=settings, base_dir=base_dir, store=store)

def create_restore_planner(settings: Settings | None = None, base_dir: Path | None = None) -> RestorePlanner:
    store = create_ops_store(settings, base_dir)
    return RestorePlanner(settings=settings, base_dir=base_dir, store=store)

def create_retention_policy_engine(settings: Settings | None = None, base_dir: Path | None = None) -> RetentionPolicyEngine:
    store = create_ops_store(settings, base_dir)
    return RetentionPolicyEngine(settings=settings, base_dir=base_dir, store=store)

def create_migration_checker(settings: Settings | None = None, base_dir: Path | None = None) -> MigrationChecker:
    store = create_ops_store(settings, base_dir)
    return MigrationChecker(settings=settings, base_dir=base_dir, store=store)

def create_operational_readiness_gate(settings: Settings | None = None, base_dir: Path | None = None) -> OperationalReadinessGate:
    store = create_ops_store(settings, base_dir)
    return OperationalReadinessGate(settings=settings, base_dir=base_dir, store=store)
