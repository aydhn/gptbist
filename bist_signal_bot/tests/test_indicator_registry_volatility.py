import pytest
from bist_signal_bot.indicators.registry import IndicatorRegistry
from bist_signal_bot.indicators.models import IndicatorCategory

@pytest.fixture
def registry():
    return IndicatorRegistry.create_default_registry()

def test_registry_contains_volatility_indicators(registry):
    assert registry.exists("atr_pct")
    assert registry.exists("normalized_true_range")
    assert registry.exists("historical_volatility")
    assert registry.exists("realized_volatility")
    assert registry.exists("parkinson_volatility")
    assert registry.exists("garman_klass_volatility")
    assert registry.exists("rogers_satchell_volatility")
    assert registry.exists("range_percent")
    assert registry.exists("gap_percent")
    assert registry.exists("bb_width_percentile")
    assert registry.exists("atr_percentile")
    assert registry.exists("volatility_zscore")
    assert registry.exists("volatility_compression")
    assert registry.exists("volatility_expansion")
    assert registry.exists("volatility_regime")
    assert registry.exists("volatility_composite")

def test_registry_list_volatility_category(registry):
    names = registry.list_names(category=IndicatorCategory.VOLATILITY)
    assert "atr_pct" in names
    assert "historical_volatility" in names
    assert "volatility_regime" in names
