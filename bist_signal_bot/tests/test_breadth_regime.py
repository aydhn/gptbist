import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthRegimeLabel, BreadthReport, BreadthScope, ParticipationSummary
)
from bist_signal_bot.breadth.regime import BreadthRegimeClassifier

def test_regime_classifier_broad_advance():
    classifier = BreadthRegimeClassifier()

    ad = AdvanceDeclineSummary(
        summary_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        advances=80, declines=20, unchanged=0, net_advances=60,
        advance_decline_ratio=4.0, advance_percent=80.0
    )

    part = ParticipationSummary(
        participation_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        participation_score=70.0
    )

    report = BreadthReport(
        report_id="1", generated_at=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        advance_decline=ad, participation=part
    )

    snapshot = classifier.classify(report)
    assert snapshot.label == BreadthRegimeLabel.BROAD_ADVANCE

def test_regime_classifier_narrow_advance():
    classifier = BreadthRegimeClassifier()

    ad = AdvanceDeclineSummary(
        summary_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        advances=55, declines=45, unchanged=0, net_advances=10,
        advance_decline_ratio=1.2, advance_percent=55.0
    )

    part = ParticipationSummary(
        participation_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        participation_score=35.0
    )

    report = BreadthReport(
        report_id="1", generated_at=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        advance_decline=ad, participation=part
    )

    snapshot = classifier.classify(report)
    assert snapshot.label == BreadthRegimeLabel.NARROW_ADVANCE
