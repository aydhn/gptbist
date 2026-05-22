import pytest
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.config.settings import Settings

def test_telegram_client_dry_run():
    settings = Settings()
    client = TelegramClient(settings)
    res = client.send_message("test", dry_run=True)
    assert res["status"] == "success"
    assert res["dry_run"] is True

def test_telegram_client_no_token_log():
    settings = Settings(TELEGRAM_BOT_TOKEN="secret_token")
    client = TelegramClient(settings)
    assert client.is_configured() is False # ENABLE_TELEGRAM_CENTER defaults false without args
