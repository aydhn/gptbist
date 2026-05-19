from datetime import datetime
from bist_signal_bot.breadth.ranking import CrossSectionalRanker
from bist_signal_bot.breadth.models import RelativeStrengthScore

def test_cross_sectional_ranking():
    ranker = CrossSectionalRanker()

    rs1 = RelativeStrengthScore(symbol="SYM1", composite_score=80.0, as_of_date=datetime.now())
    rs2 = RelativeStrengthScore(symbol="SYM2", composite_score=40.0, as_of_date=datetime.now())
    rs3 = RelativeStrengthScore(symbol="SYM3", composite_score=60.0, as_of_date=datetime.now())

    ranked = ranker.rank_symbols([rs1, rs2, rs3])

    assert len(ranked) == 3
    assert ranked[0].symbol == "SYM1"
    assert ranked[1].symbol == "SYM3"
    assert ranked[2].symbol == "SYM2"
    assert ranked[0].rank == 1
    assert ranked[2].rank == 3
