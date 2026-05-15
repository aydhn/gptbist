import re

with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

# Make sure check_quality_last_run is added to run_all_checks
if "self.check_quality_last_run()" not in content:
    content = content.replace(
        "return checks",
        "checks.append(self.check_quality_last_run())\n        return checks"
    )

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
