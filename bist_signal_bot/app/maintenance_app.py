from pathlib import Path
from bist_signal_bot.maintenance.backup import BackupManager
from bist_signal_bot.maintenance.restore import RestoreManager
from bist_signal_bot.maintenance.cleanup import CleanupManager
from bist_signal_bot.maintenance.migration import MigrationManager
from bist_signal_bot.maintenance.doctor import MaintenanceDoctor
from bist_signal_bot.maintenance.storage import MaintenanceStore
from bist_signal_bot.config.settings import get_settings

def create_maintenance_store(settings=None, base_dir: Path | None = None) -> MaintenanceStore:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    return MaintenanceStore(base_dir)

def create_backup_manager(settings=None, base_dir: Path | None = None) -> BackupManager:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    store = create_maintenance_store(settings, base_dir)
    return BackupManager(base_dir, store.get_backup_dir())

def create_restore_manager(settings=None, base_dir: Path | None = None) -> RestoreManager:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    backup_mgr = create_backup_manager(settings, base_dir)
    return RestoreManager(base_dir, backup_mgr)

def create_cleanup_manager(settings=None, base_dir: Path | None = None) -> CleanupManager:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    return CleanupManager(base_dir)

def create_migration_manager(settings=None, base_dir: Path | None = None) -> MigrationManager:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    return MigrationManager(base_dir)

def create_maintenance_doctor(settings=None, base_dir: Path | None = None) -> MaintenanceDoctor:
    settings = settings or get_settings()
    base_dir = base_dir or Path(getattr(settings, "DATA_DIR", "data"))
    return MaintenanceDoctor(base_dir)
