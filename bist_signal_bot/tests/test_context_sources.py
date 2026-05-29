import pytest
from bist_signal_bot.context_fusion.sources import ContextSourceRegistry
from bist_signal_bot.config.settings import Settings

def test_context_source_registry_weights():
    registry = ContextSourceRegistry(Settings())
    weights = registry.default_layer_weights()
    assert weights[registry.supported_layers()[0]] > 0.0
    assert len(weights) == len(registry.supported_layers())

def test_context_source_registry_optional():
    registry = ContextSourceRegistry(Settings())
    from bist_signal_bot.context_fusion.models import ContextLayer
    assert not registry.is_layer_optional(ContextLayer.TECHNICAL_SIGNAL)
    assert registry.is_layer_optional(ContextLayer.KNOWLEDGE)
