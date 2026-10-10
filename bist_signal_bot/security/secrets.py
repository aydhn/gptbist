import os
from pathlib import Path
from typing import Any, Mapping

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.models import SecretFinding, SecurityLevel
from bist_signal_bot.security.redaction import SecretRedactor
from bist_signal_bot.core.exceptions import SecretLeakError

class SecretHygieneScanner:
    """Scans settings, environment files, and payloads to ensure secret hygiene."""

    @classmethod
    def scan_settings(cls, settings: Settings, env_file: Path | None = None, example_file: Path | None = None,
                      environ: Mapping[str, str] | None = None) -> list[SecretFinding]:
        """Scans loaded Pydantic Settings for plain-text secrets."""
        # Convert settings to dict safely
        if hasattr(settings, "model_dump"):
            data = settings.model_dump()
        else:
            data = dict(settings)

        # Secrets that come from the operator's local .env / os.environ (git-ignored) are the
        # correct storage and are not leaks. Anything sourced from the tracked template
        # (.env.example) or DEFAULTS stays a finding.
        local = cls._locally_sourced_keys(env_file, example_file, environ)
        data = {k: v for k, v in data.items() if k not in local}
        return SecretRedactor.find_secret_like_values(data, source="settings")

    @staticmethod
    def _parse_env(path: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        try:
            if not path.exists():
                return out
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):]
                if "=" in line:
                    k, _, v = line.partition("=")
                    out[k.strip()] = v.strip()
        except OSError:
            pass
        return out

    @classmethod
    def _locally_sourced_keys(cls, env_file=None, example_file=None, environ=None) -> set[str]:
        """Keys whose effective value was supplied by os.environ or local .env and differs from the template."""
        from bist_signal_bot.config import settings as _cfg
        env_file = Path(env_file) if env_file else _cfg._ENV_FILE
        example_file = Path(example_file) if example_file else _cfg._ENV_EXAMPLE
        environ = os.environ if environ is None else environ
        example = cls._parse_env(example_file)
        local = cls._parse_env(env_file)
        keys: set[str] = set()
        for k in set(local) | set(example):
            raw = environ.get(k) if k in environ else local.get(k)
            if raw is None or not str(raw).strip():
                continue
            if k in example and str(raw) == example[k]:
                continue  # identical to tracked template -> still a leak
            keys.add(k)
        return keys

    @classmethod
    def scan_template_file(cls, path: Path | None = None, include_defaults: bool = True) -> list[SecretFinding]:
        """Scans the git-tracked template (.env.example) and config DEFAULTS for filled-in secrets."""
        if path is None:
            from bist_signal_bot.config import settings as _cfg
            path = _cfg._ENV_EXAMPLE
        findings = cls.scan_env_file(Path(path))
        if include_defaults:
            try:
                from bist_signal_bot.config.defaults import DEFAULTS
                findings.extend(SecretRedactor.find_secret_like_values(dict(DEFAULTS), source="defaults"))
            except Exception:
                pass
        return findings

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
                            if SecretRedactor.is_secret_key(key) and not SecretRedactor.is_non_secret_value(value, key):
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
