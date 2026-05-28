
from bist_signal_bot.factors.sector_rotation import SectorRotationAnalyzer
def test_sector_rotation():
    s = SectorRotationAnalyzer()
    res = s.analyze_sectors()
    assert res[0].sector == "TECHNOLOGY"
    assert res[0].status.value == "LEADING"

