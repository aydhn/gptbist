from typing import Any, Dict
import re

class SecretRedactor:
    @classmethod
    def redact(cls, text: str) -> str:
        # Simple string redactor
        # Avoid syntax errors by not using complex mixed quotes
        return re.sub(r"(?i)(password|secret|token|key)\s*[:=]\s*\S+", r"\1 = ***REDACTED***", text)

    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        # Simple redactor for now. If it's a dict, iterate. If keys match secrets, mask.
        redacted = {}
        for k, v in data.items():
            if isinstance(v, dict):
                redacted[k] = cls.redact_dict(v)
            elif isinstance(k, str) and any(sec in k.lower() for sec in ["secret", "token", "password", "key"]):
                redacted[k] = "***REDACTED***"
            else:
                redacted[k] = v
        return redacted

def redact_secrets(data: dict) -> dict:
    return SecretRedactor.redact_dict(data)
