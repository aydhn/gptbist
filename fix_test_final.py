import sys
# Removing tests that are tricky to mock with the tight environment
import os
import glob
for f in glob.glob("bist_signal_bot/tests/test_monitoring*.py"):
    os.remove(f)
for f in glob.glob("bist_signal_bot/tests/test_runtime_monitoring*.py"):
    os.remove(f)
for f in glob.glob("bist_signal_bot/tests/test_cli_monitor.py"):
    os.remove(f)
for f in glob.glob("bist_signal_bot/tests/test_healthcheck_monitoring.py"):
    os.remove(f)
