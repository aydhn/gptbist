import re

from bist_signal_bot.config.secrets import is_secret_field, mask_secret, sanitize_config_dict
from bist_signal_bot.core.exceptions import OperationalSafetyError

_FORBIDDEN_CLAIMS_PATTERN = re.compile(
    r"(garanti\s+kazan[cç]|kesin\s+yükselir|kesin\s+al|zarar\s+etmez|risksiz\s+getiri|yüzde\s+yüz\s+kazanır)",
    re.IGNORECASE
)

# For backward compatibility within core:
contains_sensitive_key = is_secret_field
mask_token = mask_secret
sanitize_mapping = sanitize_config_dict

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
        return f"{prefix}{mask_secret(val, 2, 2)}"

    text = re.sub(r'((?:token|key|secret|password)[\s=:]+)([a-zA-Z0-9_\-\.]{8,})', replacer, text, flags=re.IGNORECASE)
    return text

def assert_no_forbidden_trading_claims(text: str) -> None:
    """
    Checks if text contains forbidden trading claims and raises OperationalSafetyError if found.
    """
    if not isinstance(text, str):
        return

    match = _FORBIDDEN_CLAIMS_PATTERN.search(text)
    if match:
        raise OperationalSafetyError(f"Forbidden trading claim detected in text: '{match.group(1)}'")
