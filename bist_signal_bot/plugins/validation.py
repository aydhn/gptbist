from datetime import datetime
from bist_signal_bot.plugins.models import PluginManifest, PluginValidationResult, PluginStatus
from bist_signal_bot.plugins.manifest import PluginManifestParser
from bist_signal_bot.plugins.contracts import PluginContractRegistry
from bist_signal_bot.plugins.capabilities import PluginCapabilityEvaluator
from bist_signal_bot.plugins.sandbox import PluginSandboxPolicy

class PluginValidator:
    def __init__(self, parser: PluginManifestParser, contracts: PluginContractRegistry, capabilities: PluginCapabilityEvaluator, sandbox: PluginSandboxPolicy):
        self.parser = parser
        self.contracts = contracts
        self.capabilities = capabilities
        self.sandbox = sandbox

    def validate_plugin(self, manifest: PluginManifest) -> PluginValidationResult:
        result = PluginValidationResult(
            validation_id=f"val_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            status=PluginStatus.UNKNOWN,
            manifest_valid=False,
            contract_valid=False,
            capabilities_valid=False,
            hooks_valid=False,
            sandbox_valid=False
        )

        manifest_findings = self.validate_manifest(manifest)
        result.manifest_valid = len(manifest_findings) == 0
        result.findings.extend(manifest_findings)

        contract_findings = self.validate_contract(manifest)
        result.contract_valid = len(contract_findings) == 0
        result.findings.extend(contract_findings)

        cap_findings = self.validate_capabilities(manifest)
        result.capabilities_valid = len(cap_findings) == 0
        result.findings.extend(cap_findings)

        hook_findings = self.validate_hooks(manifest)
        result.hooks_valid = len(hook_findings) == 0
        result.findings.extend(hook_findings)

        sandbox_findings = self.validate_sandbox(manifest)
        result.sandbox_valid = len(sandbox_findings) == 0
        result.findings.extend(sandbox_findings)

        result.status = self.status_from_findings(result.findings)

        # Determine specific warnings
        if not result.contract_valid:
            result.warnings.append("Missing required contract fields or hooks.")
        if not result.capabilities_valid:
            result.warnings.append("Blocked capabilities detected.")
        if not result.sandbox_valid:
            result.warnings.append("Sandbox policy violations detected (e.g. unsafe imports).")

        return result

    def validate_manifest(self, manifest: PluginManifest) -> list[str]:
        return self.parser.validate_manifest_schema(manifest)

    def validate_contract(self, manifest: PluginManifest) -> list[str]:
        contract = self.contracts.contract_for_kind(manifest.kind)
        if not contract:
            return [f"No contract found for kind: {manifest.kind.value}"]
        return self.contracts.validate_manifest_against_contract(manifest, contract)

    def validate_capabilities(self, manifest: PluginManifest) -> list[str]:
        assessment = self.capabilities.assess_capabilities(manifest)
        findings = []
        if assessment.blocked_capabilities:
            findings.append(f"Blocked capabilities requested: {[c.value for c in assessment.blocked_capabilities]}")
        return findings

    def validate_hooks(self, manifest: PluginManifest) -> list[str]:
        # Simple check: hooks list shouldn't have duplicates
        if len(manifest.hooks) != len(set(manifest.hooks)):
            return ["Duplicate hooks defined in manifest."]
        return []

    def validate_sandbox(self, manifest: PluginManifest) -> list[str]:
        return self.sandbox.validate_manifest_sandbox(manifest)

    def status_from_findings(self, findings: list[str]) -> PluginStatus:
        if not findings:
            return PluginStatus.VALIDATED

        # Evaluate severity of findings
        has_fail = False
        for f in findings:
            if "Blocked capabilit" in f or "Unsafe" in f:
                return PluginStatus.BLOCKED
            if "Missing required" in f or "Missing plugin_id" in f:
                has_fail = True

        if has_fail:
            return PluginStatus.FAIL

        return PluginStatus.WATCH
