import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bist_signal_bot.cli_ux.models import CLICompatibilityResult, CLICommandContract, CLIStatus
from bist_signal_bot.cli_ux.output_contracts import CLIOutputContractRegistry

class CLICompatibilityChecker:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self.registry = CLIOutputContractRegistry(settings)

    def check_compatibility(self, sample_outputs: Optional[Dict[str, Dict[str, Any]]] = None) -> CLICompatibilityResult:
        samples = sample_outputs or self.load_sample_outputs()

        contracts_checked = 0
        compatible_count = 0
        drift_count = 0
        missing_count = 0

        for contract in self.registry.default_contracts():
            contracts_checked += 1
            output = samples.get(contract.command_path)

            if not output:
                missing_count += 1
                continue

            drift = self.detect_contract_drift(contract, output)
            if drift:
                drift_count += 1
            else:
                compatible_count += 1

        status = self.status_from_drift(drift_count, missing_count)

        return CLICompatibilityResult(
            result_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            contracts_checked=contracts_checked,
            compatible_count=compatible_count,
            drift_count=drift_count,
            missing_count=missing_count,
            status=status
        )

    def check_contract_output(self, contract: CLICommandContract, output: Dict[str, Any]) -> List[str]:
        return self.detect_contract_drift(contract, output)

    def detect_contract_drift(self, contract: CLICommandContract, output: Dict[str, Any]) -> List[str]:
        drift = []
        payload = output.get("payload", {})

        for field in contract.stable_fields:
            if field not in payload:
                drift.append(f"Missing stable field: {field}")

        return drift

    def load_sample_outputs(self) -> Dict[str, Dict[str, Any]]:
        # Mock sample loading
        return {
            "healthcheck": {"payload": {"status": "ok", "components": {}, "version": "1.0.0"}},
            "config": {"payload": {"active_profile": "test", "overrides": {}}}
        }

    def status_from_drift(self, drift_count: int, missing_count: int) -> CLIStatus:
        if drift_count > 0:
            return CLIStatus.WARNING
        if missing_count > 0:
            return CLIStatus.PARTIAL
        return CLIStatus.SUCCESS
