from bist_signal_bot.signals.fingerprint import SignalFingerprintBuilder
from bist_signal_bot.signals.models import SignalFingerprint
import json

class MockSignal:
    def __init__(self, symbol, strategy, score, direction):
        self.symbol = symbol
        self.strategy_name = strategy
        self.score = score
        self.direction = direction

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
