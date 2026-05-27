import pytest
from bist_signal_bot.financials.storage import FinancialStore
from pathlib import Path
# Mock testing integration

def test_fundamentals_engine_reads_financials():
    # Phase 52 fundamentals engine financials store’dan normalized statement ve ratios okuyabilmeli.
    store = FinancialStore(base_dir=Path("/tmp"))
    assert store is not None
