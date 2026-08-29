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

def test_normalize_payload_order_preservation():
    builder = SignalFingerprintBuilder()
    payload = {
        "z_key": 10.1234,
        "a_key": "UPPERCASE",
        "m_key": ["B", "A", 1]
    }
    normalized = builder.normalize_payload(payload)

    # Check that keys are sorted
    assert list(normalized.keys()) == ["a_key", "m_key", "z_key"]
    # Check string lowercasing
    assert normalized["a_key"] == "uppercase"
    # Check float rounding
    assert normalized["z_key"] == 10.12
    # Check list sorting and stringification
    assert normalized["m_key"] == ["1", "a", "b"]

def test_fingerprint_missing_score_fallback():
    builder = SignalFingerprintBuilder()
    s1 = MockSignal("ASELS", "trend", "NOT_A_FLOAT", "LONG", reasons=["R4", "R1", "R3", "R2"])

    fp1 = builder.build_from_signal(s1, "SCANNER", timeframe="1h")

    payload = fp1.metadata["normalized_payload"]
    assert payload.get("rounded_score_bucket") is None
    # Check major reasons are sliced to 3 and sorted/lowercased
    assert payload.get("major_reasons") == ["r1", "r3", "r4"]
