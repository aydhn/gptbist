from datetime import datetime
from bist_signal_bot.breadth.regime import BreadthRegimeClassifier
from bist_signal_bot.breadth.models import BreadthSnapshot, BreadthStatus

def test_breadth_regime_classifier():
    classifier = BreadthRegimeClassifier()

    snap = BreadthSnapshot(
        snapshot_id="1",
        as_of_date=datetime.now(),
        universe_name="U",
        symbols=[],
        composite_score=80.0
    )

    reg = classifier.classify(snap)
    assert reg.status == BreadthStatus.STRONG
    assert reg.risk_modifier == 1.0
    assert reg.signal_policy == "normal_research"

    snap.composite_score = 40.0
    reg = classifier.classify(snap)
    assert reg.status == BreadthStatus.WEAK
    assert reg.risk_modifier == 0.5
    assert reg.signal_policy == "cautious_research"
