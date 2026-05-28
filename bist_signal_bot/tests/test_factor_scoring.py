
from bist_signal_bot.factors.scoring import FactorScorer
from bist_signal_bot.factors.inputs import FactorInputBuilder
def test_factor_scoring():
    scorer = FactorScorer()
    snap = FactorInputBuilder().build_input("ASELS")
    scores = scorer.score_symbol(snap)
    assert len(scores) > 0
    agg = scorer.aggregate_scores(scores)
    assert agg is not None
