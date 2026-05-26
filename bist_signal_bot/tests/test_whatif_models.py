
import pytest
from bist_signal_bot.whatif.models import WhatIfAssumptionOverride, WhatIfScenario, AssumptionType, WhatIfScenarioType

def test_assumption_override_validation():
    with pytest.raises(ValueError):
        WhatIfAssumptionOverride(override_id="1", assumption_type=AssumptionType.COMMISSION_BPS, name="", old_value=0, new_value=1, description="d")

def test_scenario_validation():
    s = WhatIfScenario(scenario_id="1", scenario_type=WhatIfScenarioType.BASELINE, name="B", description="D")
    assert s.name == "B"
