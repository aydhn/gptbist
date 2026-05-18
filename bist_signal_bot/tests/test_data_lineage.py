import pytest
from datetime import datetime
from bist_signal_bot.data.providers_v2.lineage import DataLineageStore
from bist_signal_bot.data.providers_v2.models import DataLineageSource, ProviderType
from bist_signal_bot.config.settings import Settings

def test_lineage_store(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path))
    store = DataLineageStore(settings)

    source = DataLineageSource(
        source_id="123",
        provider_type=ProviderType.LOCAL_FILE,
        provider_name="test",
        symbol="ASELS",
        timeframe="1d",
        fetched_at=datetime.utcnow(),
        row_count=100
    )

    store.append(source)
    recent = store.load_recent("ASELS")
    assert len(recent) == 1
    assert recent[0].source_id == "123"

    latest = store.latest_for_symbol("ASELS", "1d")
    assert latest.source_id == "123"

    summary = store.lineage_summary("ASELS")
    assert summary["count"] == 1
