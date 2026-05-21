from bist_signal_bot.maintenance.models import BackupRequest, BackupScope, BackupFormat, RetentionPolicy, RetentionTarget
from datetime import datetime

def test_backup_request_defaults():
    req = BackupRequest()
    assert BackupScope.ALL_SAFE in req.scopes
    assert req.backup_format == BackupFormat.ZIP
    assert req.dry_run is False

def test_retention_policy_validation():
    policy = RetentionPolicy(
        target=RetentionTarget.LOGS,
        keep_days=30,
        keep_min_count=5
    )
    assert policy.keep_days == 30
    assert policy.keep_min_count == 5
