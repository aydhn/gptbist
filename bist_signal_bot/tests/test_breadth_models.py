from datetime import datetime
from bist_signal_bot.breadth.models import BreadthSnapshot, BreadthStatus, RelativeStrengthScore, SectorRotationScore, CrossSectionalRankItem, BreadthRegime, BreadthAnalysisRequest

def test_breadth_snapshot_summary():
    snap = BreadthSnapshot(
        snapshot_id="123",
        as_of_date=datetime(2025, 1, 1),
        universe_name="LIQUID",
        symbols=["ASELS", "THYAO"],
        composite_score=75.5,
        status=BreadthStatus.STRONG,
    )
    res = snap.summary()
    assert res["universe_name"] == "LIQUID"
    assert res["status"] == "STRONG"
    assert res["composite_score"] == 75.5

def test_relative_strength_score_creation():
    rs = RelativeStrengthScore(
        symbol="ASELS",
        as_of_date=datetime(2025,1,1),
        composite_score=80.0
    )
    assert rs.symbol == "ASELS"
    assert rs.composite_score == 80.0
