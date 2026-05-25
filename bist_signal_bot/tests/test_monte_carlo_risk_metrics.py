from bist_signal_bot.monte_carlo.risk_metrics import MonteCarloRiskAnalyzer
from bist_signal_bot.monte_carlo.models import MonteCarloPath

def test_risk_summary():
    analyzer = MonteCarloRiskAnalyzer()

    paths = [
        MonteCarloPath("p1", 0, [], [], 0, 110000.0, 10.0, 5.0, False),
        MonteCarloPath("p2", 1, [], [], 0, 60000.0, -40.0, 45.0, True),
        MonteCarloPath("p3", 2, [], [], 0, 105000.0, 5.0, 10.0, False),
        MonteCarloPath("p4", 3, [], [], 0, 95000.0, -5.0, 15.0, False),
    ]

    summary = analyzer.risk_summary(paths, 100000.0, 30.0)

    assert summary.ruin_probability_pct == 25.0
    assert summary.probability_negative_return_pct == 50.0
    assert summary.median_final_equity == 100000.0
