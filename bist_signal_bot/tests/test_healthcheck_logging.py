from bist_signal_bot.app.healthcheck import run_healthcheck


def test_healthcheck_includes_logging_and_audit():
    result = run_healthcheck()

    assert "logging_and_audit" in result
    log_audit = result["logging_and_audit"]

    assert "log_level" in log_audit
    assert "log_to_file" in log_audit
    assert "audit_enabled" in log_audit
    assert "mask_secrets_enabled" in log_audit
    assert "runtime_run_id_present" in log_audit
    assert "error_notifications_enabled" in log_audit

    # Ensure no tokens/secrets are exposed in the notification section
    notif = result["notifications"]
    assert "telegram_configured" in notif
    assert "bot_token" not in notif
    assert "chat_id" not in notif
