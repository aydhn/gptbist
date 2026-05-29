import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayer, ContextDirection, ContextStatus,
    ContextImportance, ContextSourceRef
)

def test_context_signal_normalize_symbol():
    sig = ContextSignal(
        context_id="1",
        layer=ContextLayer.TECHNICAL_SIGNAL,
        symbol="asels",
        as_of=datetime.now(timezone.utc),
        title="Test",
        direction=ContextDirection.SUPPORTIVE,
        status=ContextStatus.SUPPORT,
        importance=ContextImportance.HIGH,
        message="test"
    )
    assert sig.symbol == "ASELS"

def test_context_signal_clamp_score():
    sig = ContextSignal(
        context_id="1",
        layer=ContextLayer.TECHNICAL_SIGNAL,
        as_of=datetime.now(timezone.utc),
        title="Test",
        score=150.0,
        direction=ContextDirection.SUPPORTIVE,
        status=ContextStatus.SUPPORT,
        importance=ContextImportance.HIGH,
        message="test"
    )
    assert sig.score == 100.0

def test_context_signal_safe_message():
    sig = ContextSignal(
        context_id="1",
        layer=ContextLayer.TECHNICAL_SIGNAL,
        as_of=datetime.now(timezone.utc),
        title="Test",
        direction=ContextDirection.SUPPORTIVE,
        status=ContextStatus.SUPPORT,
        importance=ContextImportance.HIGH,
        message="Bu hisse kesin yükselir hedef fiyat 100 garanti"
    )
    # The validator replaces individual words, let's just check it doesn't contain "kesin" directly.
    assert "kesin" not in sig.message.lower()

def test_context_source_ref_safe_path():
    ref = ContextSourceRef(
        source_id="1",
        layer=ContextLayer.TECHNICAL_SIGNAL,
        object_type="file",
        source_path="/path/to/my_secret_token.txt"
    )
    assert ref.source_path == "[REDACTED]"
