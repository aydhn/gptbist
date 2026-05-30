import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.cli_ux.models import CLIOutputSchema, CLICommandContract, CLIOutputEnvelope

class CLIOutputSchemaRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self._schemas = {s.name: s for s in self.default_schemas()}

    def default_schemas(self) -> List[CLIOutputSchema]:
        return [
            CLIOutputSchema(
                schema_id=str(uuid.uuid4()),
                name="HealthcheckOutput",
                version="1.0",
                schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "components": {"type": "object"},
                        "version": {"type": "string"}
                    },
                    "required": ["status", "components", "version"]
                },
                required_fields=["status", "components", "version"]
            ),
            CLIOutputSchema(
                schema_id=str(uuid.uuid4()),
                name="ScannerOutput",
                version="1.0",
                schema={
                    "type": "object",
                    "properties": {
                        "scan_id": {"type": "string"},
                        "symbols_scanned": {"type": "integer"},
                        "signals_found": {"type": "integer"}
                    },
                    "required": ["scan_id", "symbols_scanned", "signals_found"]
                },
                required_fields=["scan_id", "symbols_scanned", "signals_found"]
            ),
             CLIOutputSchema(
                schema_id=str(uuid.uuid4()),
                name="QAReleaseGateOutput",
                version="1.0",
                schema={
                    "type": "object",
                    "properties": {
                        "gate_status": {"type": "string"},
                        "checks_passed": {"type": "integer"},
                        "checks_failed": {"type": "integer"}
                    },
                    "required": ["gate_status", "checks_passed", "checks_failed"]
                },
                required_fields=["gate_status", "checks_passed", "checks_failed"]
            ),
             CLIOutputSchema(
                schema_id=str(uuid.uuid4()),
                name="OpsStatusOutput",
                version="1.0",
                schema={
                    "type": "object",
                    "properties": {
                        "overall_status": {"type": "string"},
                        "store_status": {"type": "string"},
                        "incidents": {"type": "integer"}
                    },
                    "required": ["overall_status", "store_status", "incidents"]
                },
                required_fields=["overall_status", "store_status", "incidents"]
            ),
             CLIOutputSchema(
                schema_id=str(uuid.uuid4()),
                name="ConfigOutput",
                version="1.0",
                schema={
                    "type": "object",
                    "properties": {
                        "active_profile": {"type": "string"},
                        "overrides": {"type": "object"}
                    },
                    "required": ["active_profile", "overrides"]
                },
                required_fields=["active_profile", "overrides"]
            )
        ]

    def schema_for_contract(self, contract: CLICommandContract) -> Optional[CLIOutputSchema]:
        return self._schemas.get(contract.output_schema_name)

    def validate_output(self, envelope: CLIOutputEnvelope, schema: CLIOutputSchema) -> List[str]:
        errors = []
        if not envelope.status:
            errors.append("status is required in envelope")
        payload_errors = self.validate_required_fields(envelope.payload, schema.required_fields)
        errors.extend(payload_errors)
        return errors

    def validate_required_fields(self, payload: Dict[str, Any], required_fields: List[str]) -> List[str]:
        errors = []
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        return errors

    def safe_json_schema(self, name: str) -> Dict[str, Any]:
        schema = self._schemas.get(name)
        if schema:
            return schema.schema_obj
        return {}
