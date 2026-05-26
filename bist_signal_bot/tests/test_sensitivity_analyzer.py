
from bist_signal_bot.whatif.sensitivity import SensitivityAnalyzer
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import WhatIfScenarioResult, WhatIfScenario, WhatIfStatus, WhatIfScenarioType, AssumptionType, WhatIfAssumptionOverride
import uuid

def test_sensitivity_analyzer():
    settings = Settings()
    analyzer = SensitivityAnalyzer(settings, None)

    scen_base = WhatIfScenario(scenario_id="1", scenario_type=WhatIfScenarioType.BASELINE, name="Base", description="base")
    scen_stress = WhatIfScenario(scenario_id="2", scenario_type=WhatIfScenarioType.COST_STRESS, name="Stress", description="stress", assumptions=[
        WhatIfAssumptionOverride(override_id="x", assumption_type=AssumptionType.COMMISSION_BPS, name="x", old_value=1, new_value=2, description="x")
    ])

    baseline = WhatIfScenarioResult(result_id="1", scenario=scen_base, status=WhatIfStatus.PASS, estimated_total_cost_bps=10.0)
    scenario = WhatIfScenarioResult(result_id="2", scenario=scen_stress, status=WhatIfStatus.PASS, estimated_total_cost_bps=20.0)

    findings = analyzer.analyze(baseline, [scenario])
    assert len(findings) > 0
    assert findings[0].metric_name == "estimated_total_cost_bps"
    assert findings[0].direction.value == "WORSENS"
