import pytest
from bist_signal_bot.indicators.registry import IndicatorRegistry
from bist_signal_bot.indicators.models import IndicatorCategory
from bist_signal_bot.core.exceptions import IndicatorRegistryError
from bist_signal_bot.indicators.native import SMAIndicator

def test_registry_default():
    registry = IndicatorRegistry.create_default_registry()
    assert registry.exists("sma")
    assert registry.exists("macd")
    assert not registry.exists("unknown")

def test_registry_get_valid():
    registry = IndicatorRegistry.create_default_registry()
    ind = registry.get("SMA") # Should be case insensitive
    assert ind.spec.name == "sma"

def test_registry_get_invalid():
    registry = IndicatorRegistry.create_default_registry()
    with pytest.raises(IndicatorRegistryError):
        registry.get("unknown_indicator")

def test_registry_duplicate_register():
    registry = IndicatorRegistry.create_default_registry()
    with pytest.raises(IndicatorRegistryError):
        registry.register(SMAIndicator())

def test_registry_list_specs():
    registry = IndicatorRegistry.create_default_registry()
    specs = registry.list_specs()
    assert len(specs) >= 15 # We have at least 15 native indicators

    trend_specs = registry.list_specs(IndicatorCategory.TREND)
    trend_names = [s.name for s in trend_specs]
    assert "sma" in trend_names
    assert "macd" in trend_names
    assert "rsi" not in trend_names
