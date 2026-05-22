import pytest
from bist_signal_bot.telegram_center.digest import DigestOrchestrator
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.telegram_center.models import DigestType
from bist_signal_bot.config.settings import Settings

def test_digest_daily(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings()
    client = TelegramClient(settings)
    orch = DigestOrchestrator(store, client, settings)

    res = orch.build_daily_digest()
    assert res.request.digest_type == DigestType.DAILY
    assert res.title == "Digest DAILY"

def test_digest_chunks(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings()
    client = TelegramClient(settings)
    orch = DigestOrchestrator(store, client, settings)

    res = orch.build_daily_digest()
    assert isinstance(res.chunks, list)
