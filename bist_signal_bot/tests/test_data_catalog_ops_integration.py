import pytest
from bist_signal_bot.ops.readiness import check_readiness

def test_ops_readiness_includes_data_catalog():
    res = check_readiness(include_data_catalog=True)
    assert res["data_catalog_ready"] is True
