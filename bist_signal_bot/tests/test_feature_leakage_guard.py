from bist_signal_bot.feature_store.leakage import FeatureLeakageGuard
from bist_signal_bot.feature_store.models import FeatureFrame, FeatureQualityStatus
from datetime import datetime, timezone, timedelta

def test_feature_leakage_guard_future_timestamp():
    guard = FeatureLeakageGuard()
    now = datetime.now(timezone.utc)
    frame = FeatureFrame(
        frame_id="f1",
        feature_set_id="fs1",
        symbols=["ASELS"],
        as_of=now + timedelta(days=1),
        row_count=0, column_count=0
    )
    findings = guard.check_frame(frame, as_of=now)
    assert len(findings) == 1
    assert findings[0].status == FeatureQualityStatus.BLOCKED

def test_target_leakage():
    guard = FeatureLeakageGuard()
    findings = guard.check_target_leakage(["close", "target_return_5d"])
    assert len(findings) == 1
    assert findings[0].status == FeatureQualityStatus.BLOCKED
