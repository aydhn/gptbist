import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import (
    BreadthDivergenceType, BreadthRegimeSnapshot, BreadthReport, BreadthScope, BreadthRegimeLabel
)
from bist_signal_bot.breadth.divergence import BreadthDivergenceDetector

def test_divergence_detector_index_up_breadth_down():
    detector = BreadthDivergenceDetector()

    prev_regime = BreadthRegimeSnapshot(
        regime_id="1", as_of=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        label=BreadthRegimeLabel.BROAD_ADVANCE, breadth_score=80.0
    )

    current_regime = BreadthRegimeSnapshot(
        regime_id="2", as_of=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        label=BreadthRegimeLabel.NARROW_ADVANCE, breadth_score=75.0
    )

    report = BreadthReport(
        report_id="1", generated_at=datetime.now(), scope=BreadthScope.MARKET, scope_name="M",
        regime=current_regime
    )

    divs = detector.detect(index_returns=[1.0, 2.0], breadth_history=[prev_regime], current_report=report)

    assert len(divs) >= 1
    d = divs[0]
    assert d.divergence_type == BreadthDivergenceType.INDEX_UP_BREADTH_DOWN
    assert d.index_return_pct == 2.0
    assert d.breadth_change_pct == -5.0
