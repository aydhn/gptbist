from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import settings


def test_healthcheck_includes_notifications_section():
    settings.TELEGRAM_BOT_TOKEN = "secret_token_123"
    settings.TELEGRAM_CHAT_ID = "chat_id_456"
    settings.ENABLE_TELEGRAM = True

    summary = run_healthcheck()
    assert "notifications" in summary

    notifications = summary["notifications"]
    assert "telegram_enabled" in notifications
    assert notifications["telegram_enabled"] is True
    assert notifications["telegram_configured"] is True
    assert notifications["bot_token_configured"] is True
    assert notifications["chat_id_configured"] is True

    # Ensure raw token or chat_id is not present
    for k, v in notifications.items():
        assert str(v) != "secret_token_123"
        assert str(v) != "chat_id_456"

    # Reset for other tests
    settings.TELEGRAM_BOT_TOKEN = ""
    settings.ENABLE_TELEGRAM = False
