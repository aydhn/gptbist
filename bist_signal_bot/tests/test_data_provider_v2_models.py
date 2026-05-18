import pytest
from datetime import datetime
import pandas as pd
from bist_signal_bot.data.providers_v2.models import (
    ProviderRequest, ProviderResponse, DataFetchStatus, DataLineageSource, ProviderType,
    ImportRequest
)
from bist_signal_bot.core.exceptions import DataProviderV2Error

def test_provider_request_validation():
    with pytest.raises(DataProviderV2Error, match="timeframe cannot be empty"):
        ProviderRequest(symbols=["ASELS"], timeframe="")

    with pytest.raises(DataProviderV2Error, match="rows must be positive"):
        ProviderRequest(symbols=["ASELS"], timeframe="1d", rows=0)

    req = ProviderRequest(symbols=["asels", " thyao "], timeframe="1d")
    assert req.symbols == ["ASELS", "THYAO"]

def test_provider_response_summary():
    req = ProviderRequest(symbols=["ASELS", "THYAO"], timeframe="1d")
    res = ProviderResponse(
        request=req,
        status=DataFetchStatus.PARTIAL_SUCCESS,
        data_by_symbol={"ASELS": pd.DataFrame()},
        lineage=[],
        warnings=["Failed THYAO"],
        elapsed_seconds=1.234
    )
    summary = res.summary()
    assert summary["status"] == "PARTIAL_SUCCESS"
    assert summary["symbols_requested"] == 2
    assert summary["symbols_returned"] == 1
    assert summary["warnings_count"] == 1
    assert summary["elapsed_seconds"] == 1.234

def test_data_lineage_model():
    lin = DataLineageSource(
        source_id="123",
        provider_type=ProviderType.LOCAL_FILE,
        provider_name="test",
        symbol="ASELS",
        timeframe="1d",
        fetched_at=datetime.utcnow(),
        row_count=100
    )
    assert lin.symbol == "ASELS"

def test_import_request():
    req = ImportRequest(input_path="test.csv", timeframe="1d", format="csv", overwrite=True)
    assert req.input_path == "test.csv"
    assert req.overwrite is True
