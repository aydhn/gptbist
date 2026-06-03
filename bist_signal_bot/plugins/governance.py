from typing import Any
from datetime import datetime
from bist_signal_bot.plugins.models import PluginManifest, PluginGovernanceAssessment, PluginStatus, PluginCapabilityAssessment, PluginValidationResult

class PluginGovernanceEngine:
    def assess_plugin(self, manifest: PluginManifest) -> PluginGovernanceAssessment:
        # In a real run, this would compose results from validation, capability, etc.
        # Here we do a standalone assessment for the structure
        assessment = PluginGovernanceAssessment(
            governance_id=f"gov_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            status=PluginStatus.UNKNOWN,
            manifest_status=PluginStatus.VALIDATED,
            capability_status=PluginStatus.VALIDATED,
            validation_status=PluginStatus.VALIDATED
        )

        assessment.unsafe_language_findings = self.unsafe_language_findings(manifest.description)
        assessment.blocked_reasons = self.blocked_reasons(manifest)

        if assessment.blocked_reasons:
            assessment.status = PluginStatus.BLOCKED
            assessment.capability_status = PluginStatus.BLOCKED
        elif assessment.unsafe_language_findings:
            assessment.status = PluginStatus.WATCH
        else:
            assessment.status = PluginStatus.VALIDATED

        return assessment

    def blocked_reasons(self, manifest: PluginManifest, validation: PluginValidationResult | None = None, capability: PluginCapabilityAssessment | None = None) -> list[str]:
        reasons = []
        if validation and validation.status == PluginStatus.BLOCKED:
            reasons.append("Validation returned BLOCKED.")
        if capability and capability.status == PluginStatus.BLOCKED:
            reasons.append("Capability assessment returned BLOCKED.")
        # Check manifest capabilities explicitly
        blocked_caps = ["EXTERNAL_NETWORK", "BROKER_ACCESS", "ORDER_EXECUTION", "CLOUD_API"]
        for cap in manifest.requested_capabilities:
            if cap.value in blocked_caps:
                reasons.append(f"Requested blocked capability: {cap.value}")
        return reasons

    def unsafe_language_findings(self, text: str) -> list[str]:
        findings = []
        if not text:
            return findings
        unsafe_phrases = ["guarantee", "risk-free", "sure thing", "live ready", "broker ready", "trade ready", "al/sat"]
        lower_text = text.lower()
        for phrase in unsafe_phrases:
            if phrase in lower_text:
                findings.append(f"Contains unsafe claim: {phrase}")
        return findings

    def status_from_parts(self, manifest_status: PluginStatus, capability_status: PluginStatus, validation_status: PluginStatus, test_status: PluginStatus | None = None) -> PluginStatus:
        statuses = [manifest_status, capability_status, validation_status]
        if test_status:
            statuses.append(test_status)

        if PluginStatus.BLOCKED in statuses:
            return PluginStatus.BLOCKED
        if PluginStatus.FAIL in statuses:
            return PluginStatus.FAIL
        if PluginStatus.WATCH in statuses:
            return PluginStatus.WATCH
        if PluginStatus.DISABLED in statuses:
            return PluginStatus.DISABLED

        return PluginStatus.VALIDATED

    def governance_summary(self, assessment: PluginGovernanceAssessment) -> dict[str, Any]:
        return {
            "plugin_id": assessment.plugin_id,
            "status": assessment.status.value,
            "blocked_reasons": len(assessment.blocked_reasons),
            "unsafe_findings": len(assessment.unsafe_language_findings)
        }
