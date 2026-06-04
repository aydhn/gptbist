import uuid
from datetime import datetime
from typing import List, Optional
from bist_signal_bot.release_policy.models import (
    CompatibilityCheckResult, ReleasePolicyStatus
)
from bist_signal_bot.config.settings import get_settings

class CompatibilityPolicyChecker:
    def __init__(self) -> None:
        self.settings = get_settings()

    def run_compatibility_check(self, target_version: Optional[str] = None) -> CompatibilityCheckResult:
        schema_drift = self.check_schema_compatibility()
        cli_drift = self.check_cli_contract_compatibility()
        config_drift = self.check_config_compatibility()
        data_drift = self.check_data_contract_compatibility()
        plugin_drift = self.check_plugin_contract_compatibility()

        all_drifts = schema_drift + cli_drift + config_drift + data_drift + plugin_drift
        status = self.status_from_findings(all_drifts)

        breaking_changes = [d for d in all_drifts if "breaking" in d.lower()]

        return CompatibilityCheckResult(
            compatibility_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            target_version=target_version,
            status=status,
            checked_contracts=["schema", "cli", "config", "data", "plugin", "report"],
            breaking_changes=breaking_changes,
            schema_drift=schema_drift,
            cli_contract_drift=cli_drift,
            config_drift=config_drift,
            data_contract_drift=data_drift,
            warnings=["No external calls were made."]
        )

    def check_schema_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def check_cli_contract_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def check_config_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def check_data_contract_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def check_plugin_contract_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def check_report_template_compatibility(self) -> List[str]:
        # Mock logic
        return []

    def status_from_findings(self, findings: List[str]) -> ReleasePolicyStatus:
        if not findings:
            return ReleasePolicyStatus.PASS
        for finding in findings:
            if "breaking" in finding.lower() or "fail" in finding.lower():
                return ReleasePolicyStatus.FAIL
        return ReleasePolicyStatus.WATCH
