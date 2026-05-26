
from bist_signal_bot.whatif.capital_scaling import CapitalScalingAnalyzer
from bist_signal_bot.config.settings import Settings

def test_capital_scaling():
    settings = Settings()
    class MockEngine:
        def run_counterfactual(self, req, sc):
            from bist_signal_bot.whatif.models import WhatIfScenarioResult, WhatIfStatus
            return WhatIfScenarioResult(result_id="1", scenario=sc, status=WhatIfStatus.PASS, estimated_total_cost_bps=10.0)

    analyzer = CapitalScalingAnalyzer(settings, MockEngine(), None)
    # just testing the method doesn't crash
    scenarios = analyzer.build_notional_scenarios([50000, 100000])
    assert len(scenarios) == 2
