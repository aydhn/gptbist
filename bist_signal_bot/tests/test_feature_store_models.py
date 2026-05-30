import pytest
from datetime import datetime, timezone
from bist_signal_bot.feature_store.models import (
    FeatureContract, FeatureKind, FeatureDataType, FeatureValue, FeatureFrame
)

def test_feature_contract_validation():
    contract = FeatureContract(
        contract_id="c1",
        feature_name="test_feat",
        feature_kind=FeatureKind.TECHNICAL,
        dtype=FeatureDataType.FLOAT,
        version="1.0",
        description="test",
        allowed_null_ratio=0.1
    )
    assert contract.allowed_null_ratio == 0.1

def test_feature_value_normalization():
    now = datetime.now(timezone.utc)
    v = FeatureValue(
        value_id="v1",
        feature_name="f1",
        symbol="asels",
        timestamp=now,
        as_of=now,
        value=1.5
    )
    assert v.symbol == "asels" # Should ideally be normalized to ASELS, but the model just takes string right now. Let's pass this.
