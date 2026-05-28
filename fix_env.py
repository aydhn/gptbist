import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "pandas"])
subprocess.check_call([sys.executable, "-m", "pytest", "bist_signal_bot/tests/test_factor_models.py", "bist_signal_bot/tests/test_factor_inputs.py", "bist_signal_bot/tests/test_factor_library.py", "bist_signal_bot/tests/test_factor_scoring.py", "bist_signal_bot/tests/test_factor_exposure.py", "bist_signal_bot/tests/test_sector_rotation.py", "bist_signal_bot/tests/test_theme_exposure.py", "bist_signal_bot/tests/test_factor_crowding.py", "bist_signal_bot/tests/test_factor_attribution.py", "bist_signal_bot/tests/test_factor_storage.py"])
