from bist_signal_bot.app.monte_carlo_app import create_monte_carlo_risk_analyzer
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monte_carlo.risk_metrics import MonteCarloRiskAnalyzer

class MockSettings(Settings):
    pass

def test_create_monte_carlo_risk_analyzer():
    analyzer = create_monte_carlo_risk_analyzer()
    assert isinstance(analyzer, MonteCarloRiskAnalyzer)

def test_create_monte_carlo_risk_analyzer_with_settings():
    settings = MockSettings()
    analyzer = create_monte_carlo_risk_analyzer(settings=settings)
    assert isinstance(analyzer, MonteCarloRiskAnalyzer)
