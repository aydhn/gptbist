from datetime import datetime, timezone
import uuid
from bist_signal_bot.feature_store.models import (
    FeatureFrame, FeatureQualityAssessment, FeatureQualityFinding, FeatureQualityStatus,
    FeatureValue, FeatureContract
)

class FeatureQualityEngine:
    def assess_frame(self, frame: FeatureFrame) -> FeatureQualityAssessment:
        now = datetime.now(timezone.utc)
        return FeatureQualityAssessment(
            assessment_id=f"qa_{now.timestamp()}",
            feature_set_id=frame.feature_set_id,
            created_at=now,
            quality_score=100.0,
            status=FeatureQualityStatus.PASS
        )

    def assess_feature_values(self, values: list[FeatureValue], contract: FeatureContract | None = None) -> FeatureQualityAssessment:
        now = datetime.now(timezone.utc)
        return FeatureQualityAssessment(
            assessment_id=f"qa_val_{now.timestamp()}",
            feature_name=values[0].feature_name if values else None,
            created_at=now,
            quality_score=100.0,
            status=FeatureQualityStatus.PASS
        )

    def check_null_ratio(self, frame: FeatureFrame, contracts: list[FeatureContract]) -> list[FeatureQualityFinding]:
        findings = []
        for contract in contracts:
            null_count = 0
            total_count = len(frame.rows)
            for row in frame.rows:
                if row.get(contract.feature_name) is None:
                    null_count += 1
            if total_count > 0:
                ratio = null_count / total_count
                if contract.allowed_null_ratio is not None and ratio > contract.allowed_null_ratio:
                    findings.append(FeatureQualityFinding(
                        finding_id=str(uuid.uuid4()),
                        feature_name=contract.feature_name,
                        feature_set_id=frame.feature_set_id,
                        rule_name="null_ratio",
                        status=FeatureQualityStatus.FAIL,
                        severity="HIGH",
                        message=f"Null ratio {ratio:.2f} exceeds allowed {contract.allowed_null_ratio:.2f}"
                    ))
        return findings

    def check_value_ranges(self, frame: FeatureFrame, contracts: list[FeatureContract]) -> list[FeatureQualityFinding]:
        findings = []
        for contract in contracts:
            for row in frame.rows:
                val = row.get(contract.feature_name)
                if val is not None and isinstance(val, (int, float)):
                    if contract.min_value is not None and val < contract.min_value:
                        findings.append(FeatureQualityFinding(
                            finding_id=str(uuid.uuid4()),
                            feature_name=contract.feature_name,
                            feature_set_id=frame.feature_set_id,
                            rule_name="value_range",
                            status=FeatureQualityStatus.FAIL,
                            severity="HIGH",
                            message=f"Value {val} below minimum {contract.min_value}"
                        ))
                    if contract.max_value is not None and val > contract.max_value:
                        findings.append(FeatureQualityFinding(
                            finding_id=str(uuid.uuid4()),
                            feature_name=contract.feature_name,
                            feature_set_id=frame.feature_set_id,
                            rule_name="value_range",
                            status=FeatureQualityStatus.FAIL,
                            severity="HIGH",
                            message=f"Value {val} above maximum {contract.max_value}"
                        ))
        return findings

    def check_constant_values(self, frame: FeatureFrame) -> list[FeatureQualityFinding]:
        findings = []
        if not frame.rows:
            return findings
        for feature in frame.feature_names:
            values = [r.get(feature) for r in frame.rows if r.get(feature) is not None]
            if values and len(set(values)) == 1:
                findings.append(FeatureQualityFinding(
                    finding_id=str(uuid.uuid4()),
                    feature_name=feature,
                    feature_set_id=frame.feature_set_id,
                    rule_name="constant_value",
                    status=FeatureQualityStatus.WATCH,
                    severity="MEDIUM",
                    message="Constant value detected across frame"
                ))
        return findings

    def check_staleness(self, values: list[FeatureValue], contracts: list[FeatureContract]) -> list[FeatureQualityFinding]:
        findings = []
        now = datetime.now(timezone.utc)
        contract_map = {c.feature_name: c for c in contracts}
        for val in values:
            contract = contract_map.get(val.feature_name)
            if contract and contract.freshness_threshold_days is not None:
                days_old = (now - val.timestamp).days
                if days_old > contract.freshness_threshold_days:
                    findings.append(FeatureQualityFinding(
                        finding_id=str(uuid.uuid4()),
                        feature_name=val.feature_name,
                        rule_name="staleness",
                        status=FeatureQualityStatus.FAIL,
                        severity="HIGH",
                        message=f"Value is {days_old} days old (threshold {contract.freshness_threshold_days})"
                    ))
        return findings

    def quality_score(self, findings: list[FeatureQualityFinding]) -> float | None:
        if not findings:
            return 100.0
        score = 100.0
        for f in findings:
            if f.severity == "HIGH":
                score -= 20.0
            elif f.severity == "MEDIUM":
                score -= 10.0
            elif f.severity == "LOW":
                score -= 5.0
        return max(0.0, score)

    def status_from_score(self, score: float | None, findings: list[FeatureQualityFinding]) -> FeatureQualityStatus:
        if any(f.status == FeatureQualityStatus.BLOCKED for f in findings):
            return FeatureQualityStatus.BLOCKED
        if score is None:
            return FeatureQualityStatus.UNKNOWN
        if score >= 80:
            return FeatureQualityStatus.PASS
        elif score >= 60:
            return FeatureQualityStatus.WATCH
        return FeatureQualityStatus.FAIL
