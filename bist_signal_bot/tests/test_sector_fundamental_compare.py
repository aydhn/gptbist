import pytest
from bist_signal_bot.financials.sector_compare import SectorFinancialComparator

def test_medians_and_percentiles():
    comp = SectorFinancialComparator()
    peers = [10.0, 20.0, 30.0, 40.0, 50.0]

    rank = comp.percentile_rank(30.0, peers)
    assert rank == 40.0 # 2 items < 30.0 -> 2/5 = 40%
