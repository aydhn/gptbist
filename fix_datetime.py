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
    "bist_signal_bot/synthetic_scenarios/generator.py",
    "bist_signal_bot/synthetic_scenarios/models.py",
]

for fpath in files_to_fix:
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            text = f.read()

        text = text.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
        if "from datetime import timezone" not in text and "timezone" in text:
            text = "from datetime import timezone\n" + text

        with open(fpath, "w") as f:
            f.write(text)
