import re
from typing import Any

from bist_signal_bot.core.exceptions import OperationalSafetyError

_SENSITIVE_KEYS_PATTERN = re.compile(
    r"(token|secret|password|key|chat_?id|authorization|bearer)", re.IGNORECASE
)

_FORBIDDEN_CLAIMS_PATTERN = re.compile(
    r"(garanti\s+kazan[cç]|kesin\s+yükselir|kesin\s+al|zarar\s+etmez|risksiz\s+getiri|yüzde\s+yüz\s+kazanır)",
    re.IGNORECASE
)

def contains_sensitive_key(key: str) -> bool:
    """Checks if a string (key name) likely contains sensitive information."""
    return bool(_SENSITIVE_KEYS_PATTERN.search(str(key)))

def mask_token(token: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """Masks a token string, showing only prefix and suffix."""
    if not token or not isinstance(token, str):
        return str(token)
    if len(token) <= visible_prefix + visible_suffix:
        return "***"
    return f"{token[:visible_prefix]}...{token[-visible_suffix:]}"

def sanitize_text(text: str) -> str:
    """
    Sanitizes plain text, masking token-like substrings.
    Basic implementation masking UUIDs or long alphanumeric strings
    that might be tokens if they follow 'token=' or 'key='.
    """
    if not isinstance(text, str):
        return str(text)

    # Very basic token mask: "key=secret123" -> "key=sec...123"
    # This regex looks for key/token followed by =, : or space and then a word character sequence.
    def replacer(match):
        prefix = match.group(1)
        val = match.group(2)
        return f"{prefix}{mask_token(val, 2, 2)}"

    text = re.sub(r'((?:token|key|secret|password)[\s=:]+)([a-zA-Z0-9_\-\.]{8,})', replacer, text, flags=re.IGNORECASE)
    return text

def sanitize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes a dictionary, masking values of sensitive keys."""
    if not isinstance(mapping, dict):
        return mapping

    sanitized = {}
    for key, value in mapping.items():
        if contains_sensitive_key(key):
            sanitized[key] = mask_token(str(value))
        elif isinstance(value, dict):
            sanitized[key] = sanitize_mapping(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_mapping(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

def assert_no_forbidden_trading_claims(text: str) -> None:
    """
    Checks if text contains forbidden trading claims and raises OperationalSafetyError if found.
    """
    if not isinstance(text, str):
        return

    match = _FORBIDDEN_CLAIMS_PATTERN.search(text)
    if match:
        raise OperationalSafetyError(f"Forbidden trading claim detected in text: '{match.group(1)}'")
