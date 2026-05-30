import uuid
from typing import List, Optional
from bist_signal_bot.cli_ux.models import CLICommandContract, CommandContractType, CommandRiskLevel

class CLIOutputContractRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self._contracts = {c.command_path: c for c in self.default_contracts()}

    def default_contracts(self) -> List[CLICommandContract]:
        return [
            CLICommandContract(
                contract_id=str(uuid.uuid4()),
                command_path="healthcheck",
                contract_type=CommandContractType.HEALTHCHECK,
                description="System health status",
                output_schema_name="HealthcheckOutput",
                stable_fields=["status", "components", "version"],
                optional_fields=["details", "latency"],
                exit_codes={"SUCCESS": 0, "WARNING": 1, "FAILED": 10},
                risk_level=CommandRiskLevel.SAFE_READ_ONLY
            ),
            CLICommandContract(
                contract_id=str(uuid.uuid4()),
                command_path="config",
                contract_type=CommandContractType.CUSTOM,
                description="Configuration state",
                output_schema_name="ConfigOutput",
                stable_fields=["active_profile", "overrides"],
                optional_fields=["secrets_masked"],
                exit_codes={"SUCCESS": 0},
                risk_level=CommandRiskLevel.SAFE_READ_ONLY
            ),
            CLICommandContract(
                contract_id=str(uuid.uuid4()),
                command_path="scan symbols",
                contract_type=CommandContractType.SCANNER,
                description="Signal scanner for symbols",
                output_schema_name="ScannerOutput",
                stable_fields=["scan_id", "symbols_scanned", "signals_found"],
                optional_fields=["top_candidates", "errors"],
                exit_codes={"SUCCESS": 0, "PARTIAL": 1},
                risk_level=CommandRiskLevel.SAFE_READ_ONLY
            ),
            CLICommandContract(
                contract_id=str(uuid.uuid4()),
                command_path="qa release-gate",
                contract_type=CommandContractType.QA,
                description="QA Release Gate Check",
                output_schema_name="QAReleaseGateOutput",
                stable_fields=["gate_status", "checks_passed", "checks_failed"],
                optional_fields=["check_details"],
                exit_codes={"SUCCESS": 0, "FAILED": 1, "SAFETY_BLOCKED": 5},
                risk_level=CommandRiskLevel.SAFE_READ_ONLY
            ),
            CLICommandContract(
                contract_id=str(uuid.uuid4()),
                command_path="ops status",
                contract_type=CommandContractType.OPS,
                description="Operations status",
                output_schema_name="OpsStatusOutput",
                stable_fields=["overall_status", "store_status", "incidents"],
                optional_fields=["last_backup"],
                exit_codes={"SUCCESS": 0, "WARNING": 1},
                risk_level=CommandRiskLevel.SAFE_READ_ONLY
            )
        ]

    def get_contract(self, command_path: str) -> Optional[CLICommandContract]:
        return self._contracts.get(command_path)

    def validate_contract(self, contract: CLICommandContract) -> List[str]:
        errors = []
        if not contract.command_path:
            errors.append("command_path is required")
        if not contract.output_schema_name:
            errors.append("output_schema_name is required")
        return errors

    def contract_for_command(self, command: str) -> Optional[CLICommandContract]:
        for path, contract in self._contracts.items():
            if command.startswith(path):
                return contract
        return None

    def required_stable_fields(self, command_path: str) -> List[str]:
        contract = self.get_contract(command_path)
        if contract:
            return contract.stable_fields
        return []
