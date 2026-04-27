import json
import pytest
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditEvent, AuditEventType, AuditLogger

def test_audit_event_validation():
    with pytest.raises(ValueError, match="cannot be empty"):
        AuditEvent(event_type=AuditEventType.SYSTEM, message="")

    event = AuditEvent(event_type=AuditEventType.SYSTEM, message="Test", symbol="asels")
    assert event.symbol == "ASELS"

def test_audit_logger_disabled(tmp_path):
    settings = Settings(ENABLE_AUDIT_LOG=False, LOG_DIR=str(tmp_path))
    logger = AuditLogger(settings)

    logger.log_app_start()

    # Check that no file was created
    audit_file = tmp_path / settings.AUDIT_LOG_FILE_NAME
    assert not audit_file.exists()

def test_audit_logger_writes_jsonl(tmp_path):
    settings = Settings(ENABLE_AUDIT_LOG=True, LOG_DIR=str(tmp_path), AUDIT_LOG_FILE_NAME="audit.log")
    logger = AuditLogger(settings)

    logger.log_app_start(run_id="test_run", metadata={"env": "test"})

    audit_file = tmp_path / "audit.log"
    assert audit_file.exists()

    with open(audit_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["event_type"] == "APP_START"
        assert data["message"] == "Application started"
        assert data["run_id"] == "test_run"
        assert data["metadata"]["env"] == "test"
        assert "timestamp" in data

def test_audit_logger_sanitizes_metadata(tmp_path):
    settings = Settings(ENABLE_AUDIT_LOG=True, LOG_DIR=str(tmp_path), MASK_SECRETS_IN_LOGS=True)
    logger = AuditLogger(settings)

    event = AuditEvent(
        event_type=AuditEventType.SYSTEM,
        message="Test secret",
        metadata={"api_key": "secret123456789"}
    )
    logger.log_event(event)

    audit_file = tmp_path / settings.AUDIT_LOG_FILE_NAME
    with open(audit_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readlines()[0])
        assert data["metadata"]["api_key"] == "secr...6789"
