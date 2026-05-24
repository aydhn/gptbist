import uuid
from typing import Any

from bist_signal_bot.config_registry.models import (
    ConfigChangeDecision,
    ConfigDefinition,
    ConfigModule,
    ConfigSafetyLevel,
    ConfigValidationFinding,
    ConfigValidationStatus,
    ConfigValueType,
)


class ConfigSchemaBuilder:
    def __init__(self):
        self._definitions: dict[str, ConfigDefinition] = {}

    def build_default_schema(self) -> list[ConfigDefinition]:
        defs = []

        # Forbidden items
        defs.append(ConfigDefinition(
            key="BROKER_ENABLED",
            module=ConfigModule.CORE,
            value_type=ConfigValueType.BOOLEAN,
            default_value=False,
            description="Enable broker API integration",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        ))
        defs.append(ConfigDefinition(
            key="REAL_ORDER_ENABLED",
            module=ConfigModule.CORE,
            value_type=ConfigValueType.BOOLEAN,
            default_value=False,
            description="Enable real order execution",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        ))
        defs.append(ConfigDefinition(
            key="ENABLE_LIVE_TRADING",
            module=ConfigModule.CORE,
            value_type=ConfigValueType.BOOLEAN,
            default_value=False,
            description="Enable live trading mode",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        ))
        defs.append(ConfigDefinition(
            key="ALLOW_HTML_SCRAPING",
            module=ConfigModule.DATA,
            value_type=ConfigValueType.BOOLEAN,
            default_value=False,
            description="Allow HTML scraping for data",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        ))
        defs.append(ConfigDefinition(
            key="ENABLE_PAID_APIS",
            module=ConfigModule.DATA,
            value_type=ConfigValueType.BOOLEAN,
            default_value=False,
            description="Enable paid API integrations",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        ))

        # Sensitive items
        defs.append(ConfigDefinition(
            key="TELEGRAM_BOT_TOKEN",
            module=ConfigModule.TELEGRAM,
            value_type=ConfigValueType.SECRET,
            default_value="",
            description="Telegram Bot API Token",
            safety_level=ConfigSafetyLevel.SENSITIVE,
            secret=True
        ))
        defs.append(ConfigDefinition(
            key="TELEGRAM_ALLOWED_CHAT_IDS",
            module=ConfigModule.TELEGRAM,
            value_type=ConfigValueType.SECRET,
            default_value=[],
            description="Allowed Telegram Chat IDs",
            safety_level=ConfigSafetyLevel.SENSITIVE,
            secret=True
        ))
        defs.append(ConfigDefinition(
            key="OPENAI_API_KEY",
            module=ConfigModule.ML,
            value_type=ConfigValueType.SECRET,
            default_value="",
            description="OpenAI API Key for analysis",
            safety_level=ConfigSafetyLevel.SENSITIVE,
            secret=True
        ))

        # Safe items
        defs.append(ConfigDefinition(
            key="ENABLE_AUDIT_LOG",
            module=ConfigModule.GOVERNANCE,
            value_type=ConfigValueType.BOOLEAN,
            default_value=True,
            description="Enable audit logging",
            safety_level=ConfigSafetyLevel.SAFE
        ))
        defs.append(ConfigDefinition(
            key="RESEARCH_LAB_MAX_JOBS",
            module=ConfigModule.RESEARCH_LAB,
            value_type=ConfigValueType.INTEGER,
            default_value=10,
            description="Max concurrent jobs in research lab",
            safety_level=ConfigSafetyLevel.CAUTION,
            min_value=1,
            max_value=100
        ))

        # Add flags to definition map
        self._definitions = {d.key: d for d in defs}
        return defs

    def definition_for_key(self, key: str) -> ConfigDefinition | None:
        if not self._definitions:
            self.build_default_schema()
        # Fallback for dynamic secrets
        if key not in self._definitions:
            k_lower = key.lower()
            if any(s in k_lower for s in ["token", "secret", "password", "key"]) and "public" not in k_lower:
                return ConfigDefinition(
                    key=key,
                    module=ConfigModule.UNKNOWN,
                    value_type=ConfigValueType.SECRET,
                    default_value="",
                    description=f"Auto-detected secret for {key}",
                    safety_level=ConfigSafetyLevel.SENSITIVE,
                    secret=True
                )
        return self._definitions.get(key)

    def definitions_by_module(self, module: ConfigModule) -> list[ConfigDefinition]:
        if not self._definitions:
            self.build_default_schema()
        return [d for d in self._definitions.values() if d.module == module]

    def validate_schema(self, definitions: list[ConfigDefinition]) -> list[ConfigValidationFinding]:
        findings = []
        keys_seen = set()

        for d in definitions:
            if d.key in keys_seen:
                findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Duplicate Config Key",
                    message=f"Duplicate definition found for key {d.key}",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_TYPE_ERROR,
                    key=d.key,
                    module=d.module
                ))
            keys_seen.add(d.key)

            # Check secret definition
            if d.secret and d.safety_level not in [ConfigSafetyLevel.SENSITIVE, ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.FORBIDDEN]:
                findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Invalid Secret Safety Level",
                    message=f"Secret key {d.key} must have SENSITIVE or higher safety level",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_SECRET_LEAK,
                    key=d.key,
                    module=d.module
                ))

            # Check forbidden definition
            if d.safety_level == ConfigSafetyLevel.FORBIDDEN:
                if d.default_value is not False and d.default_value is not None and d.default_value != "" and d.default_value != []:
                    findings.append(ConfigValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        title="Invalid Forbidden Default",
                        message=f"Forbidden key {d.key} must have safe default (False, None, empty)",
                        status=ConfigValidationStatus.FAIL,
                        decision=ConfigChangeDecision.BLOCK_FORBIDDEN,
                        key=d.key,
                        module=d.module
                    ))

            # Check ENUM definition
            if d.value_type == ConfigValueType.ENUM and not d.enum_values:
                findings.append(ConfigValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    title="Missing Enum Values",
                    message=f"Enum key {d.key} must specify enum_values",
                    status=ConfigValidationStatus.FAIL,
                    decision=ConfigChangeDecision.BLOCK_TYPE_ERROR,
                    key=d.key,
                    module=d.module
                ))

        return findings
