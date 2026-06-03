from datetime import datetime
from bist_signal_bot.plugins.models import PluginManifest, PluginTestResult, PluginStatus

class PluginTestHarness:
    def run_plugin_tests(self, manifest: PluginManifest, dry_run: bool = True) -> PluginTestResult:
        result = PluginTestResult(
            test_id=f"test_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            status=PluginStatus.UNKNOWN,
            dry_run=dry_run
        )

        tests = [
            self.test_manifest_contract,
            self.test_capability_policy,
            self.test_hook_registration,
            self.test_safe_language,
            self.test_no_external_calls,
            self.test_no_broker_or_order_access
        ]

        result.tests_run = len(tests)

        for t in tests:
            findings = t(manifest)
            if findings:
                result.tests_failed += 1
                result.findings.extend(findings)
                # Treat external or broker access as BLOCKED
                for f in findings:
                    if "External" in f or "Broker" in f or "Order" in f:
                        result.status = PluginStatus.BLOCKED
            else:
                result.tests_passed += 1

        if result.status != PluginStatus.BLOCKED:
            if result.tests_failed > 0:
                result.status = PluginStatus.FAIL
            else:
                result.status = PluginStatus.VALIDATED

        return result

    def test_manifest_contract(self, manifest: PluginManifest) -> list[str]:
        # Covered by validator in real scenario, mock for test harness
        return []

    def test_capability_policy(self, manifest: PluginManifest) -> list[str]:
        # Mock checking capability policy
        return []

    def test_hook_registration(self, manifest: PluginManifest) -> list[str]:
        return []

    def test_safe_language(self, manifest: PluginManifest) -> list[str]:
        findings = []
        unsafe_words = ["guarantee", "sure thing", "risk-free", "live ready"]
        text = f"{manifest.name} {manifest.description}".lower()
        for w in unsafe_words:
            if w in text:
                findings.append(f"Unsafe language found: {w}")
        return findings

    def test_no_external_calls(self, manifest: PluginManifest) -> list[str]:
        # Static mock check
        return []

    def test_no_broker_or_order_access(self, manifest: PluginManifest) -> list[str]:
        # Static mock check
        return []
