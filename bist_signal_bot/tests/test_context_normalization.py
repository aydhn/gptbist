import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.normalization import ContextNormalizer
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayer, ContextDirection, ContextStatus, ContextImportance
)
from bist_signal_bot.config.settings import Settings

def test_normalize_score():
    normalizer = ContextNormalizer(Settings())
    # Normal scoring layer
    assert normalizer.normalize_score(150.0, ContextLayer.TECHNICAL_SIGNAL) == 100.0
    assert normalizer.normalize_score(-10.0, ContextLayer.TECHNICAL_SIGNAL) == 0.0
    # Risk/Pressure layers should be inverted if direction is not supportive
    assert normalizer.normalize_score(80.0, ContextLayer.RISK, ContextDirection.NEGATIVE) == 20.0

def test_status_from_score():
    normalizer = ContextNormalizer(Settings())
    assert normalizer.status_from_score(80.0, ContextDirection.SUPPORTIVE) == ContextStatus.STRONG_SUPPORT
    assert normalizer.status_from_score(60.0, ContextDirection.SUPPORTIVE) == ContextStatus.SUPPORT
    assert normalizer.status_from_score(30.0, ContextDirection.NEGATIVE) == ContextStatus.PRESSURE
    assert normalizer.status_from_score(10.0, ContextDirection.NEGATIVE) == ContextStatus.HIGH_PRESSURE
