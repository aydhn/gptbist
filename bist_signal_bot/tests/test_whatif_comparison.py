
from bist_signal_bot.whatif.comparison import WhatIfComparisonEngine
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import WhatIfScenarioResult, WhatIfScenario, WhatIfStatus, WhatIfScenarioType

def test_comparison_engine():
    settings = Settings()
    engine = WhatIfComparisonEngine(settings, None)

    scen_base = WhatIfScenario(scenario_id="1", scenario_type=WhatIfScenarioType.BASELINE, name="Base", description="base")
    baseline = WhatIfScenarioResult(result_id="1", scenario=scen_base, status=WhatIfStatus.PASS, estimated_net_quality_score=50.0)

    comp = engine.compare([baseline])
    assert comp.best_scenario_id == "1"
