import uuid
from datetime import datetime, UTC

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config_registry.models import (
    ConfigChangeDecision,
    ConfigDefinition,
    ConfigModule,
    ConfigSafetyLevel,
    ConfigValidationFinding,
    ConfigValidationResult,
    ConfigValidationStatus,
    ConfigValueRecord,
    ConfigValueType,
    FeatureFlag
)


class ConfigValidator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def validate_all(self, records: list[ConfigValueRecord] | None = None, flags: list[FeatureFlag] | None = None) -> ConfigValidationResult:
        records = records or []
        flags = flags or []
        findings = []

        for record in records:
            findings.extend(self.validate_record(record))

        findings.extend(self.validate_runtime_safety(records))

        blocked = sum(1 for f in findings if f.decision.name.startswith("BLOCK"))
        warnings = sum(1 for f in findings if f.decision == ConfigChangeDecision.WARN)
        status = ConfigValidationStatus.FAIL if blocked > 0 else (ConfigValidationStatus.WARN if warnings > 0 else ConfigValidationStatus.PASS)

        return ConfigValidationResult(
            validation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            status=status,
            records_checked=len(records),
            findings=findings,
            blocked_count=blocked,
            warning_count=warnings,
            pass_count=len(records) - blocked - warnings
        )

    def validate_record(self, record: ConfigValueRecord, definition: ConfigDefinition | None = None) -> list[ConfigValidationFinding]:
        findings = []
        if type_finding := self.validate_type(record, definition):
            findings.append(type_finding)
        if range_finding := self.validate_range(record, definition):
            findings.append(range_finding)
        if forbidden_finding := self.validate_forbidden_values(record):
            findings.append(forbidden_finding)
        if secret_finding := self.validate_secret_hygiene(record):
            findings.append(secret_finding)
        return findings

    def validate_type(self, record: ConfigValueRecord, definition: ConfigDefinition | None = None) -> ConfigValidationFinding | None:
        if record.value_type == ConfigValueType.BOOLEAN and not isinstance(record.value, bool):
            return ConfigValidationFinding(
                finding_id=str(uuid.uuid4()),
                title="Type Mismatch",
                message=f"Key {record.key} expects BOOLEAN but got {type(record.value).__name__}",
                status=ConfigValidationStatus.FAIL,
                decision=ConfigChangeDecision.BLOCK_TYPE_ERROR,
                key=record.key,
                module=record.module
            )
        # Add more type validation logic here
        return None

    def validate_range(self, record: ConfigValueRecord, definition: ConfigDefinition | None = None) -> ConfigValidationFinding | None:
        if definition and definition.min_value is not None and isinstance(record.value, (int, float)):
            if record.value < definition.min_value:
                return ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Range Mismatch",
                    message=f"Key {record.key} value {record.value} is below min {definition.min_value}",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_TYPE_ERROR,
                    key=record.key,
                    module=record.module
                )
        return None

    def validate_secret_hygiene(self, record: ConfigValueRecord) -> ConfigValidationFinding | None:
        if record.is_secret and "raw" in str(record.value_redacted).lower():
            # A bit contrived, but represents checking for leak attempts
            return ConfigValidationFinding(
                finding_id=str(uuid.uuid4()),
                title="Secret Hygiene Violation",
                message=f"Key {record.key} appears to be exposing raw secret in redacted output",
                status=ConfigValidationStatus.FAIL,
                decision=ConfigChangeDecision.BLOCK_SECRET_LEAK,
                key=record.key,
                module=record.module
            )
        return None

    def validate_forbidden_values(self, record: ConfigValueRecord) -> ConfigValidationFinding | None:
        forbidden_keys = [
            "BROKER_ENABLED", "REAL_ORDER_ENABLED", "ENABLE_LIVE_TRADING",
            "ALLOW_HTML_SCRAPING", "ENABLE_PAID_APIS"
        ]
        if record.key in forbidden_keys and record.value is True:
            return ConfigValidationFinding(
                finding_id=str(uuid.uuid4()),
                title="Forbidden Action Allowed",
                message=f"Key {record.key} is enabling a forbidden action",
                status=ConfigValidationStatus.FAIL,
                decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                key=record.key,
                module=record.module
            )
        return None

    def validate_runtime_safety(self, records: list[ConfigValueRecord]) -> list[ConfigValidationFinding]:
        findings = []
        for record in records:
            if record.key == "BROKER_ENABLED" and record.value is True:
                 findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Broker Enabled Check",
                    message=f"Broker integration is strictly forbidden",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                    key=record.key
                ))
            if record.key == "REAL_ORDER_ENABLED" and record.value is True:
                findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Real Order Enabled Check",
                    message=f"Real order execution is strictly forbidden",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                    key=record.key
                ))
            if record.key == "ENABLE_LIVE_TRADING" and record.value is True:
                 findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Live Trading Enabled Check",
                    message=f"Live trading is strictly forbidden",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                    key=record.key
                ))
            if record.key == "ALLOW_HTML_SCRAPING" and record.value is True:
                 findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="HTML Scraping Check",
                    message=f"HTML scraping is strictly forbidden",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                    key=record.key
                ))
            if record.key == "ENABLE_PAID_APIS" and record.value is True:
                 findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Paid API Check",
                    message=f"Paid API calls are strictly forbidden",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                    key=record.key
                ))
        return findings
