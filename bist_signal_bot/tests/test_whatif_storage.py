
from bist_signal_bot.whatif.storage import WhatIfStore
from bist_signal_bot.config.settings import Settings

def test_whatif_store(tmp_path):
    settings = Settings()
    store = WhatIfStore(settings, base_dir=tmp_path)
    assert store.runs_dir.exists()
