from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.models import SecretFinding, SecurityLevel
from bist_signal_bot.security.redaction import SecretRedactor
from bist_signal_bot.core.exceptions import SecretLeakError

class SecretHygieneScanner:
    """Scans settings, environment files, and payloads to ensure secret hygiene."""

    @classmethod
    def scan_settings(cls, settings: Settings) -> list[SecretFinding]:
        """Scans loaded Pydantic Settings for plain-text secrets."""
        # Convert settings to dict safely
        if hasattr(settings, "model_dump"):
            data = settings.model_dump()
        else:
            data = dict(settings)

        return SecretRedactor.find_secret_like_values(data, source="settings")

    @classmethod
    def scan_env_file(cls, path: Path) -> list[SecretFinding]:
        """Reads a .env file and scans for plain-text secrets."""
        if not path.exists():
            return []

        findings = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            key, value = parts[0].strip(), parts[1].strip()
                            if SecretRedactor.is_secret_key(key) and value:
                                findings.extend(SecretRedactor.find_secret_like_values({key: value}, source=f"{path.name}:{line_idx+1}"))
                            elif SecretRedactor.contains_secret(value):
                                findings.extend(SecretRedactor.find_secret_like_values({key: value}, source=f"{path.name}:{line_idx+1}"))
        except Exception as e:
            pass

        return findings

    @classmethod
    def scan_report_payload(cls, payload: dict[str, Any]) -> list[SecretFinding]:
        """Scans a report/audit payload to ensure no secrets are leaked."""
        return SecretRedactor.find_secret_like_values(payload, source="payload")

    @classmethod
    def validate_no_secret_leak(cls, payload: Any, context: str) -> None:
        """Throws a SecretLeakError if a secret is found in the payload."""
        if SecretRedactor.contains_secret(payload):
             # Try to find exactly what leaked for the error message, but mask it
             findings = SecretRedactor.find_secret_like_values(payload, source=context)
             keys_leaked = [f.key for f in findings]
             raise SecretLeakError(f"Secret leak detected in {context}. Keys implicated: {keys_leaked}")

    @classmethod
    def safe_settings_summary(cls, settings: Settings) -> dict[str, Any]:
        """Returns a sanitized dict of the application settings."""
        if hasattr(settings, "model_dump"):
            data = settings.model_dump()
        else:
            data = dict(settings)
        return SecretRedactor.redact_dict(data)
