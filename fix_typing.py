import os

files_to_fix = [
    "bist_signal_bot/synthetic_scenarios/ohlcv.py",
    "bist_signal_bot/synthetic_scenarios/macro.py",
    "bist_signal_bot/synthetic_scenarios/breadth.py",
    "bist_signal_bot/synthetic_scenarios/financials.py",
    "bist_signal_bot/synthetic_scenarios/events.py",
    "bist_signal_bot/synthetic_scenarios/disclosures.py",
    "bist_signal_bot/synthetic_scenarios/features.py",
    "bist_signal_bot/synthetic_scenarios/models_fixture.py",
    "bist_signal_bot/synthetic_scenarios/portfolio.py",
    "bist_signal_bot/synthetic_scenarios/stress.py",
    "bist_signal_bot/synthetic_scenarios/edge_cases.py",
    "bist_signal_bot/synthetic_scenarios/manifest.py",
    "bist_signal_bot/synthetic_scenarios/validation.py",
]

for fpath in files_to_fix:
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            text = f.read()
        if "from typing import Any" not in text:
            text = "from typing import Any\n" + text
        with open(fpath, "w") as f:
            f.write(text)
