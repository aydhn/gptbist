from bist_signal_bot.monte_carlo.scoring import MonteCarloRobustnessScorer
from bist_signal_bot.monte_carlo.models import MonteCarloRiskSummary, RealityCheckResult, RealityCheckStatus, MonteCarloStatus

def test_scoring_robustness():
    scorer = MonteCarloRobustnessScorer()

    risk = MonteCarloRiskSummary("s1", ruin_probability_pct=0.0, probability_negative_return_pct=10.0)
    rc = RealityCheckResult("r1", RealityCheckStatus.ROBUST, "ret", 1)

    score = scorer.score(risk, rc, [])
    assert score == 100.0
    assert scorer.derive_status(score, []) == MonteCarloStatus.PASS

def test_scoring_overfit():
    scorer = MonteCarloRobustnessScorer()

    risk = MonteCarloRiskSummary("s1", ruin_probability_pct=30.0, probability_negative_return_pct=50.0)
    rc = RealityCheckResult("r1", RealityCheckStatus.LIKELY_OVERFIT, "ret", 1)

    score = scorer.score(risk, rc, [])
    assert score == 0.0
    assert scorer.derive_status(score, []) == MonteCarloStatus.FAIL
