from bist_signal_bot.signals.fingerprint import SignalFingerprintBuilder
from bist_signal_bot.signals.models import SignalFingerprint
import json

class MockSignal:
    def __init__(self, symbol, strategy, score, direction, decision=None, reasons=None):
        self.symbol = symbol
        self.strategy_name = strategy
        self.score = score
        self.direction = direction
        if decision:
            self.decision = decision
        if reasons:
            self.reasons = reasons

def test_fingerprint_deterministic_hash():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("ASELS", "trend", 75.4, "LONG")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "SCANNER")

    assert fp1.fingerprint_id == fp2.fingerprint_id

def test_fingerprint_small_score_change():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("ASELS", "trend", 75.43, "LONG")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "SCANNER")

    assert fp1.fingerprint_id == fp2.fingerprint_id
    assert builder.is_same_family(fp1, fp2)

def test_fingerprint_strategy_change():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("ASELS", "momentum", 75.4, "LONG")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "SCANNER")

    assert fp1.fingerprint_id != fp2.fingerprint_id
    assert not builder.is_same_family(fp1, fp2)

def test_fingerprint_with_consensus_decision():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG", decision="STRONG_BUY", reasons=["high volume"])

    fp1 = builder.build_from_signal(s1, "SCANNER")
    assert fp1.metadata["normalized_payload"].get("consensus_decision") == "strong_buy"
    assert "major_reasons" in fp1.metadata["normalized_payload"]

def test_is_same_family_different_symbol():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("GARAN", "trend", 75.4, "LONG")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "SCANNER")

    assert not builder.is_same_family(fp1, fp2)

def test_is_same_family_different_direction():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("ASELS", "trend", 75.4, "SHORT")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "SCANNER")

    assert not builder.is_same_family(fp1, fp2)

def test_is_same_family_different_source_type():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", 75.4, "LONG")
    s2 = MockSignal("ASELS", "trend", 75.4, "LONG")

    fp1 = builder.build_from_signal(s1, "SCANNER")
    fp2 = builder.build_from_signal(s2, "PORTFOLIO")

    assert not builder.is_same_family(fp1, fp2)
