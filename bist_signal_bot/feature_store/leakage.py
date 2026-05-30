from datetime import datetime, timezone
import uuid
from bist_signal_bot.feature_store.models import (
    FeatureFrame, FeatureValue, FeatureLeakageFinding, FeatureLeakageType, FeatureQualityStatus, FeatureDefinition, FeatureContract
)

class FeatureLeakageGuard:
    def check_frame(self, frame: FeatureFrame, as_of: datetime | None = None) -> list[FeatureLeakageFinding]:
        findings = []
        check_time = as_of or datetime.now(timezone.utc)
        if frame.as_of > check_time:
            findings.append(FeatureLeakageFinding(
                leakage_id=str(uuid.uuid4()),
                feature_name="frame",
                leakage_type=FeatureLeakageType.FUTURE_TIMESTAMP,
                as_of=frame.as_of,
                severity="CRITICAL",
                message=f"Frame as_of time {frame.as_of} is in the future relative to {check_time}",
                status=FeatureQualityStatus.BLOCKED
            ))
        return findings

    def check_value(self, value: FeatureValue) -> list[FeatureLeakageFinding]:
        findings = []
        if value.timestamp > value.as_of:
            findings.append(FeatureLeakageFinding(
                leakage_id=str(uuid.uuid4()),
                feature_name=value.feature_name,
                leakage_type=FeatureLeakageType.FUTURE_TIMESTAMP,
                symbol=value.symbol,
                timestamp=value.timestamp,
                as_of=value.as_of,
                severity="CRITICAL",
                message=f"Value timestamp {value.timestamp} is after as_of {value.as_of}",
                status=FeatureQualityStatus.BLOCKED
            ))
        return findings

    def check_target_leakage(self, feature_names: list[str]) -> list[FeatureLeakageFinding]:
        findings = []
        for name in feature_names:
            if "target" in name.lower() or "forward" in name.lower() or "future" in name.lower():
                findings.append(FeatureLeakageFinding(
                    leakage_id=str(uuid.uuid4()),
                    feature_name=name,
                    leakage_type=FeatureLeakageType.TARGET_LEAKAGE,
                    severity="CRITICAL",
                    message="Target label or future feature used in input frame",
                    status=FeatureQualityStatus.BLOCKED
                ))
        return findings

    def check_lookahead_window(self, feature: FeatureDefinition, contract: FeatureContract | None = None) -> list[FeatureLeakageFinding]:
        findings = []
        if contract and contract.leakage_sensitive:
            findings.append(FeatureLeakageFinding(
                leakage_id=str(uuid.uuid4()),
                feature_name=feature.feature_name,
                leakage_type=FeatureLeakageType.LOOKAHEAD_WINDOW,
                severity="HIGH",
                message="Feature is marked as leakage sensitive",
                status=FeatureQualityStatus.WATCH
            ))
        return findings

    def check_same_day_close_usage(self, feature_names: list[str], context: str | None = None) -> list[FeatureLeakageFinding]:
        findings = []
        if context == "intraday":
            for name in feature_names:
                if "close" in name.lower() and "prev" not in name.lower():
                    findings.append(FeatureLeakageFinding(
                        leakage_id=str(uuid.uuid4()),
                        feature_name=name,
                        leakage_type=FeatureLeakageType.SAME_DAY_CLOSE_IN_INTRADAY_CONTEXT,
                        severity="MEDIUM",
                        message="Same-day close used in intraday context may cause leakage",
                        status=FeatureQualityStatus.WATCH
                    ))
        return findings

    def classify_leakage(self, findings: list[FeatureLeakageFinding]) -> FeatureQualityStatus:
        if not findings:
            return FeatureQualityStatus.PASS
        if any(f.status == FeatureQualityStatus.BLOCKED for f in findings):
            return FeatureQualityStatus.BLOCKED
        if any(f.severity == "HIGH" for f in findings):
            return FeatureQualityStatus.FAIL
        return FeatureQualityStatus.WATCH
