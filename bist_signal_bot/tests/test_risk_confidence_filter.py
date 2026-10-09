from types import SimpleNamespace

from bist_signal_bot.risk.filters import SignalScoreFilter
from bist_signal_bot.risk.models import RiskRejectReason


def _run(conf, min_conf):
    sig = SimpleNamespace(score=80.0, confidence=conf)
    s = SimpleNamespace(RISK_MIN_SIGNAL_SCORE=0.5, RISK_MIN_CONFIDENCE=min_conf)
    return SignalScoreFilter().evaluate(sig, None, None, None, None, s)


def test_unset_confidence_is_skipped_with_warning():
    rejects, warns = _run(0.0, 0.5)
    assert RiskRejectReason.CONFIDENCE_TOO_LOW not in rejects
    assert any("confidence_not_provided" in w for w in warns)


def test_fraction_threshold_applies_to_percent_scale():
    assert RiskRejectReason.CONFIDENCE_TOO_LOW in _run(30.0, 0.5)[0]
    assert RiskRejectReason.CONFIDENCE_TOO_LOW not in _run(60.0, 0.5)[0]
