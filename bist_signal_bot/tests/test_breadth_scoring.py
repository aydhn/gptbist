import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthDivergence, BreadthDivergenceType, BreadthReport, BreadthScope
)
from bist_signal_bot.breadth.scoring import BreadthScorer

def test_breadth_scorer_basic():
    scorer = BreadthScorer()

    ad = AdvanceDeclineSummary(
        summary_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        advances=80, declines=20, unchanged=0, net_advances=60,
        advance_decline_ratio=4.0, advance_percent=80.0
    )

    report = BreadthReport(
        report_id="1", generated_at=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        advance_decline=ad
    )

    score = scorer.score_report(report)
    assert score == 80.0

def test_breadth_scorer_divergence_penalty():
    scorer = BreadthScorer()

    ad = AdvanceDeclineSummary(
        summary_id="1", scope=BreadthScope.MARKET, scope_name="M", as_of=datetime.now(),
        advances=80, declines=20, unchanged=0, net_advances=60,
        advance_decline_ratio=4.0, advance_percent=80.0
    )

    div = BreadthDivergence(
        divergence_id="1", as_of=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        divergence_type=BreadthDivergenceType.INDEX_UP_BREADTH_DOWN,
        divergence_score=80.0 # This triggers penalty > 60
    )

    report = BreadthReport(
        report_id="1", generated_at=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        advance_decline=ad, divergences=[div]
    )

    score = scorer.score_report(report)
    assert score == 70.0 # 80 - 10 penalty
