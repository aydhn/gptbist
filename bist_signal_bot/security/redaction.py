import re
from typing import Any
from copy import deepcopy

from bist_signal_bot.security.models import SecretFinding, SecretClassification, SecurityLevel

class SecretRedactor:
    """Handles masking and redacting of sensitive secrets in strings and data structures."""

    # Patterns indicating potential secrets. Not exhaustive, but catches obvious leaks.
    SECRET_KEY_PATTERNS = re.compile(r'(api[_-]?key|token|password|secret|chat[_-]?id)', re.IGNORECASE)

    # 123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789
    TELEGRAM_TOKEN_PATTERN = re.compile(r'\b\d{8,10}:[a-zA-Z0-9_-]{35}\b')
    BEARER_TOKEN_PATTERN = re.compile(r'Bearer\s+([a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
    PRIVATE_KEY_PATTERN = re.compile(r'-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE)
    CONNECTION_STRING_PATTERN = re.compile(r'(postgresql|mysql|mongodb\+srv|redis)://[^:]+:[^@]+@', re.IGNORECASE)
    LONG_RANDOM_PATTERN = re.compile(r'\b[A-Za-z0-9_-]{32,}\b')

    # BIST symbols that are 5 chars long, avoid masking these if they get picked up as random
    # Though 32+ chars pattern avoids this anyway. Just adding safety.
    SAFE_WORDS = {"ASELS", "THYAO", "GARAN", "AKBNK", "YKBNK"}

    @classmethod
    def mask_value(cls, value: str, visible_prefix: int = 3, visible_suffix: int = 2) -> str:
        """Masks a secret string, revealing only prefix and suffix if possible."""
        if not value or not isinstance(value, str):
            return str(value)

        length = len(value)
        if length <= visible_prefix + visible_suffix:
            return "***"

        return f"{value[:visible_prefix]}...{value[-visible_suffix:]}"

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Finds and redacts common secret patterns in a string."""
        if not isinstance(text, str) or not text:
            return str(text)

        redacted = text

        # Telegram tokens
        for match in cls.TELEGRAM_TOKEN_PATTERN.finditer(redacted):
            redacted = redacted.replace(match.group(0), cls.mask_value(match.group(0)))

        # Bearer tokens
        for match in cls.BEARER_TOKEN_PATTERN.finditer(redacted):
            redacted = redacted.replace(match.group(1), cls.mask_value(match.group(1)))

        # Private Keys
        if cls.PRIVATE_KEY_PATTERN.search(redacted):
             # Hard redact the whole block if a private key is detected
             redacted = re.sub(r'-----BEGIN.*PRIVATE KEY-----.*?-----END.*PRIVATE KEY-----', '***REDACTED_PRIVATE_KEY***', redacted, flags=re.DOTALL|re.IGNORECASE)

        # Connection Strings
        for match in cls.CONNECTION_STRING_PATTERN.finditer(redacted):
            # Try to mask the password part only, simple replace for now
            redacted = redacted.replace(match.group(0), "masked_connection_string://")

        # Simple key-value string (e.g. BOT_TOKEN=123456:ABCSECRET)
        for match in re.finditer(r'([a-zA-Z0-9_-]+)\s*=\s*([^\s]{8,})', redacted):
            key = match.group(1)
            val = match.group(2)
            if cls.SECRET_KEY_PATTERNS.search(key):
                 redacted = redacted.replace(val, cls.mask_value(val))

        return redacted

    @classmethod
    def is_secret_key(cls, key: str) -> bool:
        if not isinstance(key, str):
            return False
        return bool(cls.SECRET_KEY_PATTERNS.search(key))

    @classmethod
    def redact_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively masks secret values in a configuration dictionary."""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if cls.is_secret_key(str(key)):
                if isinstance(value, str):
                     sanitized[key] = cls.mask_value(value)
                else:
                     sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                sanitized[key] = cls.redact_list(value)
            elif isinstance(value, str):
                sanitized[key] = cls.redact_text(value)
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def redact_list(cls, items: list[Any]) -> list[Any]:
        sanitized = []
        for item in items:
            if isinstance(item, dict):
                sanitized.append(cls.redact_dict(item))
            elif isinstance(item, list):
                sanitized.append(cls.redact_list(item))
            elif isinstance(item, str):
                sanitized.append(cls.redact_text(item))
            else:
                sanitized.append(item)
        return sanitized

    @classmethod
    def contains_secret(cls, text_or_obj: Any) -> bool:
        """Checks if the object contains obvious secret strings (like telegram tokens)."""
        if isinstance(text_or_obj, str):
            if cls.TELEGRAM_TOKEN_PATTERN.search(text_or_obj):
                return True
            if cls.BEARER_TOKEN_PATTERN.search(text_or_obj):
                return True
            if cls.PRIVATE_KEY_PATTERN.search(text_or_obj):
                return True
            if cls.CONNECTION_STRING_PATTERN.search(text_or_obj):
                return True
            return False
        elif isinstance(text_or_obj, dict):
            for k, v in text_or_obj.items():
                if cls.is_secret_key(str(k)) and v is not None and str(v).strip() != "":
                    # Allow already masked strings like ***
                    if isinstance(v, str) and "***" in v:
                        continue
                    return True
                if cls.contains_secret(v):
                    return True
            return False
        elif isinstance(text_or_obj, list):
            for item in text_or_obj:
                if cls.contains_secret(item):
                    return True
            return False
        return False

    @classmethod
    def find_secret_like_values(cls, data: Any, source: str = "unknown") -> list[SecretFinding]:
        findings = []
        if isinstance(data, dict):
            for k, v in data.items():
                if cls.is_secret_key(str(k)) and v is not None and str(v).strip() != "" and "***" not in str(v):
                    classification = SecretClassification.TOKEN
                    if "password" in str(k).lower(): classification = SecretClassification.PASSWORD
                    elif "chat" in str(k).lower(): classification = SecretClassification.CHAT_ID
                    elif "api" in str(k).lower(): classification = SecretClassification.API_KEY

                    findings.append(SecretFinding(
                        key=str(k),
                        classification=classification,
                        masked_value=cls.mask_value(str(v)),
                        source=source,
                        severity=SecurityLevel.HIGH
                    ))
                findings.extend(cls.find_secret_like_values(v, source=f"{source}.{k}"))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                findings.extend(cls.find_secret_like_values(item, source=f"{source}[{i}]"))
        elif isinstance(data, str):
             if cls.TELEGRAM_TOKEN_PATTERN.search(data):
                  findings.append(SecretFinding(
                        key="regex_match",
                        classification=SecretClassification.TOKEN,
                        masked_value="***",
                        source=source,
                        severity=SecurityLevel.HIGH
                  ))
        return findings
