import pytest
from datetime import datetime
from pathlib import Path
from bist_signal_bot.breadth.models import BreadthRegimeSnapshot, BreadthRegimeLabel, BreadthScope
from bist_signal_bot.breadth.storage import BreadthStore
from bist_signal_bot.config.settings import Settings

def test_breadth_store_append(tmp_path):
    settings = Settings()
    store = BreadthStore(settings=settings, base_dir=tmp_path)

    snapshot = BreadthRegimeSnapshot(
        regime_id="1", as_of=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        label=BreadthRegimeLabel.BROAD_ADVANCE
    )

    path = store.append_regime(snapshot)
    assert path.exists()
    assert path.stat().st_size > 0
