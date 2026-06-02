import os
from pathlib import Path

# Wait, `run_dbg2.py` is printing "Col close Values before to_numeric:" and "Col close Type before numeric:".
# These print statements are NOT in `bist_signal_bot/data_import/normalization.py`. They are IN `run_dbg2.py` itself!
# Ah! In `run_dbg2.py`, it was explicitly running the old logic!
# Let's run the actual test to see if it passes now.
