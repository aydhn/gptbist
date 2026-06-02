import os
with open("bist_signal_bot/synthetic_scenarios/library.py", "r") as f:
    text = f.read()

text = text.replace("def spec_summary(self, spec: SyntheticScenarioSpec) -> dict[str, Any]:", "def spec_summary(self, spec: SyntheticScenarioSpec) -> dict[str, 'Any']:")
with open("bist_signal_bot/synthetic_scenarios/library.py", "w") as f:
    f.write("from typing import Any\n" + text)
