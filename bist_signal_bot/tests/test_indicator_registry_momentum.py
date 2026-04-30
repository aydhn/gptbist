import pytest
from bist_signal_bot.indicators.registry import IndicatorRegistry
from bist_signal_bot.indicators.models import IndicatorCategory

def test_registry_contains_momentum_indicators():
    registry = IndicatorRegistry.create_default_registry()

    momentum_names = [
        "momentum", "roc_pct", "rsi_enhanced", "stoch_enhanced", "williams_r",
        "cci", "mfi", "tsi", "ultimate_osc", "ppo", "kst", "connors_rsi",
        "momentum_strength"
    ]

    for name in momentum_names:
        assert registry.exists(name), f"Indicator {name} should be registered"

        ind = registry.get(name)
        assert ind.spec.category == IndicatorCategory.MOMENTUM, f"Indicator {name} category should be MOMENTUM"

def test_registry_list_momentum_category():
    registry = IndicatorRegistry.create_default_registry()
    momentum_specs = registry.list_specs(IndicatorCategory.MOMENTUM)
    momentum_names = [s.name for s in momentum_specs]

    assert "rsi_enhanced" in momentum_names
    assert "cci" in momentum_names
    assert "momentum_strength" in momentum_names

    assert "sma" not in momentum_names # SMA is TREND
