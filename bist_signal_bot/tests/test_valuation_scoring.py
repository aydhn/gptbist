from bist_signal_bot.valuation.scoring import ValuationScorer
from bist_signal_bot.valuation.models import ValuationStatus

def test_valuation_scoring_logic():
    scorer = ValuationScorer()

    # Check baseline status mappings
    assert scorer._status_to_score(ValuationStatus.EXTREME_CHEAP) == 0.0
    assert scorer._status_to_score(ValuationStatus.CHEAP) == 25.0
    assert scorer._status_to_score(ValuationStatus.FAIR) == 50.0

    parts = {
        "hist": 25.0,
        "peer": 50.0,
        "qual": 80.0,
        "data": 100.0
    }
    score = scorer.combine_scores(parts)
    # hist weight 0.40 * 25 = 10
    # peer weight 0.35 * 50 = 17.5
    # sum = 27.5 / 0.75 = 36.666
    # It is < 50, quality > 70, no penalty.
    assert 36.0 < score < 37.0
