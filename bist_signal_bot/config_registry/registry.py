from typing import Any
import uuid

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config_registry.models import (
    ConfigValueRecord,
    ConfigValueType,
    ConfigModule,
    ConfigSafetyLevel
)
from bist_signal_bot.config_registry.schema import ConfigSchemaBuilder
from bist_signal_bot.security.redaction import SecretRedactor


class ConfigRegistry:
    def __init__(self, schema_builder: ConfigSchemaBuilder, settings: Settings, redactor: SecretRedactor | None = None, logger=None):
        self.schema_builder = schema_builder
        self.settings = settings
        self.redactor = redactor or SecretRedactor()
        self.logger = logger
        self._records: dict[str, ConfigValueRecord] = {}

    def load_records(self) -> list[ConfigValueRecord]:
        definitions = self.schema_builder.build_default_schema()
        records = []

        for d in definitions:
            val = getattr(self.settings, d.key, d.default_value)
            redacted_val = "***REDACTED***" if d.secret else val

            records.append(ConfigValueRecord(
                key=d.key,
                value=val,
                value_redacted=redacted_val,
                source="ENV" if hasattr(self.settings, d.key) else "DEFAULT",
                module=d.module,
                value_type=d.value_type,
                safety_level=d.safety_level,
                is_default=(val == d.default_value),
                is_secret=d.secret,
                valid=True
            ))

        self._records = {r.key: r for r in records}
        return records

    def get_record(self, key: str) -> ConfigValueRecord | None:
        if not self._records:
            self.load_records()
        return self._records.get(key)

    def list_records(self, module: ConfigModule | None = None, include_secrets: bool = False) -> list[ConfigValueRecord]:
        if not self._records:
            self.load_records()
        recs = list(self._records.values())
        if module:
            recs = [r for r in recs if r.module == module]
        if not include_secrets:
            # Secrets are redacted anyway in value_redacted, but if user explicitly doesn't want them in list
            pass
        return recs

    def set_value(self, key: str, value: Any, confirm: bool = False) -> ConfigValueRecord:
        # Mock logic, as it shouldn't persist to .env
        d = self.schema_builder.definition_for_key(key)
        if not d:
            raise ValueError(f"Unknown config key: {key}")

        if d.safety_level in [ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.SENSITIVE] and not confirm:
            raise ValueError(f"Changing {key} requires confirmation")

        if d.safety_level == ConfigSafetyLevel.FORBIDDEN:
             raise ValueError(f"Cannot modify FORBIDDEN config {key}")

        redacted_val = "***REDACTED***" if d.secret else value

        rec = ConfigValueRecord(
            key=key,
            value=value,
            value_redacted=redacted_val,
            source="OVERRIDE",
            module=d.module,
            value_type=d.value_type,
            safety_level=d.safety_level,
            is_default=(value == d.default_value),
            is_secret=d.secret,
            valid=True
        )
        self._records[key] = rec
        return rec

    def redacted_summary(self) -> dict[str, Any]:
        if not self._records:
            self.load_records()
        return {k: v.value_redacted for k, v in self._records.items()}

    def export_redacted_config(self) -> dict[str, Any]:
        return self.redacted_summary()
