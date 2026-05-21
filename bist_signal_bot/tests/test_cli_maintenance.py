import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.commands_maintenance import (
    handle_backup_create, handle_restore, handle_cleanup, handle_migrate_apply, handle_doctor
)

class FakeArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch('bist_signal_bot.cli.commands_maintenance.create_backup_manager')
@patch('bist_signal_bot.cli.commands_maintenance.create_maintenance_store')
def test_cli_backup_create_dry_run(mock_store, mock_create):
    mock_mgr = MagicMock()
    mock_res = MagicMock()
    mock_res.status.value = "SUCCESS"
    mock_res.manifest.included_files = 5
    mock_res.output_path = None
    mock_mgr.create_backup.return_value = mock_res
    mock_create.return_value = mock_mgr

    args = FakeArgs(scope=None, format="ZIP", verify=False, dry_run=True, json=False)
    handle_backup_create(args)

    mock_mgr.create_backup.assert_called_once()
    mock_store.assert_not_called()

@patch('bist_signal_bot.cli.commands_maintenance.create_restore_manager')
def test_cli_restore_requires_confirm(mock_create):
    mock_mgr = MagicMock()
    mock_res = MagicMock()
    mock_res.status.value = "SUCCESS"
    mock_mgr.restore.return_value = mock_res
    mock_create.return_value = mock_mgr

    args = FakeArgs(backup="test.zip", scope=None, dry_run=False, confirm=False, json=False)
    handle_restore(args)

    mock_mgr.restore.assert_called_once()
    call_args = mock_mgr.restore.call_args[1]
    assert call_args['confirm'] is False

@patch('bist_signal_bot.cli.commands_maintenance.create_cleanup_manager')
def test_cli_cleanup_requires_confirm(mock_create):
    mock_mgr = MagicMock()
    mock_res = MagicMock()
    mock_mgr.analyze.return_value = mock_res
    mock_create.return_value = mock_mgr

    args = FakeArgs(target=None, dry_run=False, confirm=False, json=False)
    handle_cleanup(args)

    mock_mgr.apply_cleanup.assert_not_called()

@patch('bist_signal_bot.cli.commands_maintenance.create_maintenance_doctor')
@patch('bist_signal_bot.cli.commands_maintenance.create_maintenance_store')
def test_cli_doctor(mock_store, mock_create):
    mock_doc = MagicMock()
    mock_res = MagicMock()
    mock_res.status.value = "SUCCESS"
    mock_res.missing_dirs = []
    mock_res.corrupted_files = []
    mock_res.secret_risk_files = []
    mock_doc.run_doctor.return_value = mock_res
    mock_create.return_value = mock_doc

    args = FakeArgs(deep=False, json=False)
    handle_doctor(args)

    mock_doc.run_doctor.assert_called_once()
