from datetime import datetime
from bist_signal_bot.plugins.models import PluginManifest, PluginCapabilityKind, PluginCapabilityAssessment, PluginStatus, PluginKind

class PluginCapabilityEvaluator:
    def assess_capabilities(self, manifest: PluginManifest) -> PluginCapabilityAssessment:
        assessment = PluginCapabilityAssessment(
            assessment_id=f"cap_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            requested_capabilities=manifest.requested_capabilities,
            status=PluginStatus.UNKNOWN
        )

        allowed = []
        blocked = []

        default_allowed = self.default_allowed_capabilities(manifest.kind)
        globally_blocked = self.blocked_capabilities()

        for cap in manifest.requested_capabilities:
            if cap in globally_blocked:
                blocked.append(cap)
            elif cap in default_allowed:
                allowed.append(cap)
            else:
                # If not explicitly allowed for this kind, block it for safety
                blocked.append(cap)

        assessment.allowed_capabilities = allowed
        assessment.blocked_capabilities = blocked
        assessment.status = self.capability_status(assessment)

        if blocked:
            assessment.warnings.append(f"Blocked capabilities: {', '.join(c.value for c in blocked)}")

        return assessment

    def default_allowed_capabilities(self, kind: PluginKind) -> list[PluginCapabilityKind]:
        # Mapping based on PluginContract allowed_capabilities
        mapping = {
            PluginKind.STRATEGY: [PluginCapabilityKind.REGISTER_STRATEGY, PluginCapabilityKind.READ_LOCAL_FILES],
            PluginKind.SIGNAL: [],
            PluginKind.INDICATOR: [],
            PluginKind.FEATURE: [PluginCapabilityKind.REGISTER_FEATURE],
            PluginKind.DATA_IMPORT_ADAPTER: [PluginCapabilityKind.REGISTER_DATA_ADAPTER, PluginCapabilityKind.READ_LOCAL_FILES],
            PluginKind.REPORT_SECTION: [PluginCapabilityKind.REGISTER_REPORT_SECTION],
            PluginKind.SYNTHETIC_SCENARIO: [PluginCapabilityKind.REGISTER_SYNTHETIC_SCENARIO],
            PluginKind.MARKET_DEFINITION: [PluginCapabilityKind.REGISTER_MARKET],
            PluginKind.VALIDATION_RULE: [PluginCapabilityKind.REGISTER_VALIDATION_RULE],
            PluginKind.MAINTENANCE_ACTION: [PluginCapabilityKind.RUN_DRY_RUN_COMMAND, PluginCapabilityKind.READ_LOCAL_FILES],
            PluginKind.LOCAL_UI_PAGE: [PluginCapabilityKind.REGISTER_UI_PAGE],
            PluginKind.ORCHESTRATOR_TASK: [PluginCapabilityKind.RUN_DRY_RUN_COMMAND],
        }
        return mapping.get(kind, [])

    def blocked_capabilities(self) -> list[PluginCapabilityKind]:
        return [
            PluginCapabilityKind.EXTERNAL_NETWORK,
            PluginCapabilityKind.BROKER_ACCESS,
            PluginCapabilityKind.ORDER_EXECUTION,
            PluginCapabilityKind.CLOUD_API
        ]

    def is_capability_allowed(self, kind: PluginKind, capability: PluginCapabilityKind) -> bool:
        if capability in self.blocked_capabilities():
            return False
        return capability in self.default_allowed_capabilities(kind)

    def capability_status(self, assessment: PluginCapabilityAssessment) -> PluginStatus:
        if assessment.blocked_capabilities:
            return PluginStatus.BLOCKED
        return PluginStatus.VALIDATED
