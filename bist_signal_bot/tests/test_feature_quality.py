from bist_signal_bot.feature_store.quality import FeatureQualityEngine
from bist_signal_bot.feature_store.models import FeatureFrame, FeatureContract, FeatureKind, FeatureDataType
from datetime import datetime, timezone

def test_quality_engine_score():
    engine = FeatureQualityEngine()
    frame = FeatureFrame(
        frame_id="f1",
        feature_set_id="fs1",
        symbols=["ASELS"],
        as_of=datetime.now(timezone.utc),
        row_count=1,
        column_count=1,
        rows=[{"f1": None}]
    )
    contract = FeatureContract(contract_id="c1", feature_name="f1", feature_kind=FeatureKind.TECHNICAL, dtype=FeatureDataType.FLOAT, version="1.0", description="test", allowed_null_ratio=0.0)
    findings = engine.check_null_ratio(frame, [contract])
    assert len(findings) == 1
    score = engine.quality_score(findings)
    assert score == 80.0
