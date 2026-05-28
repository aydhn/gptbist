import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pytest", "bist_signal_bot/tests/test_sector_rotation.py", "bist_signal_bot/tests/test_theme_exposure.py", "bist_signal_bot/tests/test_cli_factors.py"])
