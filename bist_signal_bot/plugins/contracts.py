from typing import Any
from bist_signal_bot.plugins.models import PluginContract, PluginKind, PluginHookKind, PluginCapabilityKind, PluginManifest

class PluginContractRegistry:
    def default_contracts(self) -> list[PluginContract]:
        return [
            PluginContract(
                contract_id="strategy_plugin_v1",
                kind=PluginKind.STRATEGY,
                required_fields=["entrypoint", "module_path"],
                required_hooks=[PluginHookKind.STRATEGY_DISCOVERY],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_STRATEGY, PluginCapabilityKind.READ_LOCAL_FILES],
                required_tests=["test_capability_policy", "test_hook_registration"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="signal_plugin_v1",
                kind=PluginKind.SIGNAL,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.SIGNAL_DISCOVERY],
                allowed_capabilities=[],
                required_tests=["test_safe_language"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="indicator_plugin_v1",
                kind=PluginKind.INDICATOR,
                required_fields=["entrypoint"],
                required_hooks=[],
                allowed_capabilities=[],
                required_tests=[],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="feature_plugin_v1",
                kind=PluginKind.FEATURE,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.FEATURE_COMPUTE],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_FEATURE],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="data_import_adapter_plugin_v1",
                kind=PluginKind.DATA_IMPORT_ADAPTER,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.DATA_IMPORT_PREVIEW],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_DATA_ADAPTER, PluginCapabilityKind.READ_LOCAL_FILES],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="report_section_plugin_v1",
                kind=PluginKind.REPORT_SECTION,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.REPORT_SECTION_RENDER],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_REPORT_SECTION],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="synthetic_scenario_plugin_v1",
                kind=PluginKind.SYNTHETIC_SCENARIO,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.SYNTHETIC_GENERATE],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_SYNTHETIC_SCENARIO],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="market_definition_plugin_v1",
                kind=PluginKind.MARKET_DEFINITION,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.MARKET_REGISTER],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_MARKET],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="validation_rule_plugin_v1",
                kind=PluginKind.VALIDATION_RULE,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.VALIDATION_RULE_RUN],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_VALIDATION_RULE],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="maintenance_action_plugin_v1",
                kind=PluginKind.MAINTENANCE_ACTION,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.MAINTENANCE_ACTION_RUN],
                allowed_capabilities=[PluginCapabilityKind.RUN_DRY_RUN_COMMAND, PluginCapabilityKind.READ_LOCAL_FILES],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="local_ui_page_plugin_v1",
                kind=PluginKind.LOCAL_UI_PAGE,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.LOCAL_UI_PAGE_RENDER],
                allowed_capabilities=[PluginCapabilityKind.REGISTER_UI_PAGE],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
            PluginContract(
                contract_id="orchestrator_task_plugin_v1",
                kind=PluginKind.ORCHESTRATOR_TASK,
                required_fields=["entrypoint"],
                required_hooks=[PluginHookKind.ORCHESTRATOR_TASK_RUN],
                allowed_capabilities=[PluginCapabilityKind.RUN_DRY_RUN_COMMAND],
                required_tests=["test_capability_policy"],
                version="1.0.0"
            ),
        ]

    def contract_for_kind(self, kind: PluginKind) -> PluginContract | None:
        for c in self.default_contracts():
            if c.kind == kind:
                return c
        return None

    def validate_contract(self, contract: PluginContract) -> list[str]:
        findings = []
        if not contract.contract_id:
            findings.append("Missing contract_id")
        if not contract.kind:
            findings.append("Missing kind")
        return findings

    def validate_manifest_against_contract(self, manifest: PluginManifest, contract: PluginContract) -> list[str]:
        findings = []
        for field in contract.required_fields:
            val = getattr(manifest, field, None)
            if not val:
                findings.append(f"Missing required field: {field}")

        for hook in contract.required_hooks:
            if hook not in manifest.hooks:
                findings.append(f"Missing required hook: {hook}")

        for cap in manifest.requested_capabilities:
            if cap not in contract.allowed_capabilities:
                findings.append(f"Blocked capability for contract: {cap}")

        return findings

    def contract_summary(self, contract: PluginContract) -> dict[str, Any]:
        return {
            "contract_id": contract.contract_id,
            "kind": contract.kind.value,
            "version": contract.version,
            "required_fields": contract.required_fields,
            "required_hooks": [h.value for h in contract.required_hooks],
            "allowed_capabilities": [c.value for c in contract.allowed_capabilities]
        }
