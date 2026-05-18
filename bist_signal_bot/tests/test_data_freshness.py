import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from bist_signal_bot.data.freshness import DataFreshnessChecker
from bist_signal_bot.data.providers_v2.models import DataLineageSource, ProviderType

def test_freshness_checker():
    mock_store = MagicMock()

    # Mock ASELS as fresh
    fresh_lin = DataLineageSource(
        source_id="1", provider_type=ProviderType.LOCAL_FILE, provider_name="p",
        symbol="ASELS", timeframe="1d", fetched_at=datetime.utcnow() - timedelta(hours=10), row_count=1
    )

    # Mock THYAO as stale
    stale_lin = DataLineageSource(
        source_id="2", provider_type=ProviderType.LOCAL_FILE, provider_name="p",
        symbol="THYAO", timeframe="1d", fetched_at=datetime.utcnow() - timedelta(hours=50), row_count=1
    )

    def side_effect(symbol, tf):
        if symbol == "ASELS": return fresh_lin
        if symbol == "THYAO": return stale_lin
        return None

    mock_store.latest_for_symbol.side_effect = side_effect

    checker = DataFreshnessChecker(lineage_store=mock_store)
    report = checker.check_symbols(["ASELS", "THYAO", "GARAN"], "1d", max_age_hours=48.0)

    assert "ASELS" in report.fresh_symbols
    assert "THYAO" in report.stale_symbols
    assert "GARAN" in report.missing_symbols
