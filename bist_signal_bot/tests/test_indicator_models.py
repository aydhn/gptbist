import pytest
from pydantic import ValidationError
from bist_signal_bot.indicators.models import (
    IndicatorSpec, IndicatorCategory, IndicatorBackend,
    IndicatorRequest, IndicatorResult, IndicatorBatchResult, IndicatorIssue
)

def test_indicator_spec_valid():
    spec = IndicatorSpec(
        name="sma",
        display_name="Simple Moving Average",
        category=IndicatorCategory.TREND,
        backend=IndicatorBackend.NATIVE,
        required_columns=["close"],
        default_params={"window": 20},
        output_columns=["sma"],
        min_rows=20
    )
    assert spec.name == "sma"

def test_indicator_spec_invalid_name():
    with pytest.raises(ValidationError):
        IndicatorSpec(
            name="SMA", # Should be lowercase
            display_name="Simple Moving Average",
            category=IndicatorCategory.TREND,
            backend=IndicatorBackend.NATIVE,
            required_columns=["close"],
            default_params={"window": 20},
            output_columns=["sma"],
            min_rows=20
        )
    with pytest.raises(ValidationError):
        IndicatorSpec(
            name="simple ma", # No spaces
            display_name="Simple Moving Average",
            category=IndicatorCategory.TREND,
            backend=IndicatorBackend.NATIVE,
            required_columns=["close"],
            default_params={"window": 20},
            output_columns=["sma"],
            min_rows=20
        )

def test_indicator_spec_invalid_min_rows():
    with pytest.raises(ValidationError):
        IndicatorSpec(
            name="sma",
            display_name="Simple Moving Average",
            category=IndicatorCategory.TREND,
            backend=IndicatorBackend.NATIVE,
            required_columns=["close"],
            default_params={"window": 20},
            output_columns=["sma"],
            min_rows=-5
        )

def test_indicator_request_name_normalization():
    req = IndicatorRequest(name=" SMA ")
    assert req.name == "sma"

def test_indicator_batch_result_summary():
    import pandas as pd
    res = IndicatorResult(
        indicator="sma",
        status="SUCCESS",
        output_columns=["sma_20"],
        row_count=100,
        nan_count=19,
        elapsed_seconds=0.1
    )
    batch = IndicatorBatchResult(
        results=[res],
        output_data=pd.DataFrame(),
        requested_count=1,
        success_count=1,
        failed_count=0,
        elapsed_seconds=0.1
    )
    summary = batch.summary()
    assert summary["requested_count"] == 1
    assert summary["success_count"] == 1
    assert len(summary["results"]) == 1
    assert summary["results"][0]["indicator"] == "sma"
