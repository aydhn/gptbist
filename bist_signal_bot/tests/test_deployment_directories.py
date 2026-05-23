import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.directories import DeploymentDirectoryManager
from bist_signal_bot.deployment.models import DeploymentStatus

def test_directory_manager_required_dirs(tmp_path):
    settings = Settings()
    manager = DeploymentDirectoryManager(settings, tmp_path)
    dirs = manager.required_directories()
    assert len(dirs) > 10

def test_directory_manager_dry_run(tmp_path):
    settings = Settings()
    manager = DeploymentDirectoryManager(settings, tmp_path)
    results = manager.init_directories(confirm=False, dry_run=True)

    assert all(r.status == DeploymentStatus.SKIPPED for r in results)

    dirs = manager.required_directories()
    for d in dirs:
        assert not d.exists()

def test_directory_manager_confirm(tmp_path):
    settings = Settings()
    manager = DeploymentDirectoryManager(settings, tmp_path)
    results = manager.init_directories(confirm=True, dry_run=False)

    assert all(r.status == DeploymentStatus.PASS for r in results)

    dirs = manager.required_directories()
    for d in dirs:
        assert d.exists()
