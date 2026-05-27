import pytest
from bist_signal_bot.financials.storage import FinancialStore

def test_storage_init(tmp_path):
    store = FinancialStore(base_dir=tmp_path)
    assert store.base_dir == tmp_path
