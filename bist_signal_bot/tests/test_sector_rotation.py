from datetime import datetime
from bist_signal_bot.breadth.sector_rotation import SectorRotationAnalyzer
from bist_signal_bot.breadth.models import RelativeStrengthScore, SectorRotationStatus

def test_sector_rotation_analyzer():
    analyzer = SectorRotationAnalyzer()

    rs1 = RelativeStrengthScore(symbol="SYM1", composite_score=80.0, as_of_date=datetime.now())
    rs2 = RelativeStrengthScore(symbol="SYM2", composite_score=20.0, as_of_date=datetime.now())

    sectors = {"SYM1": "SEC_A", "SYM2": "SEC_B"}

    res = analyzer.calculate_sector_rotation([rs1, rs2], sectors)
    assert len(res) == 2

    sec_a = next(r for r in res if r.sector == "SEC_A")
    sec_b = next(r for r in res if r.sector == "SEC_B")

    assert sec_a.rotation_status == SectorRotationStatus.LEADING
    assert sec_b.rotation_status == SectorRotationStatus.LAGGING
