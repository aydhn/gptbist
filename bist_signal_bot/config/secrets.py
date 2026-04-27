from typing import Any

SECRET_FIELD_NAMES = {
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chat_id",
    "telegram_bot_token",
    "telegram_chat_id",
}

def is_secret_field(name: str) -> bool:
    """Checks if a field name likely implies a secret value."""
    name_lower = str(name).lower()
    return any(secret_term in name_lower for secret_term in SECRET_FIELD_NAMES)

def mask_secret(value: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """Masks a secret string, revealing only prefix and suffix if possible."""
    if not value or not isinstance(value, str):
        return str(value)

    length = len(value)
    if length <= visible_prefix + visible_suffix:
        return "***"

    return f"{value[:visible_prefix]}...{value[-visible_suffix:]}"

def sanitize_config_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively masks secret values in a configuration dictionary."""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if is_secret_field(key):
            sanitized[key] = mask_secret(str(value))
        elif isinstance(value, dict):
            sanitized[key] = sanitize_config_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_config_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

def settings_safe_dump(settings: Any) -> dict[str, Any]:
    """
    Dumps the settings object to a dictionary and masks secret fields.
    Takes `Any` to avoid circular import with Settings, but expects a Pydantic model.
    """
    if hasattr(settings, "model_dump"):
        data = settings.model_dump()
    elif hasattr(settings, "dict"):
        data = settings.dict()
    else:
        # Fallback for plain objects/dicts
        data = dict(settings) if isinstance(settings, dict) else vars(settings)

    return sanitize_config_dict(data)

def validate_telegram_secrets(settings: Any) -> None:
    """
    Validates that Telegram secrets are provided if Telegram is enabled and not in dry run.
    Expects settings object.
    """
    from bist_signal_bot.core.exceptions import TelegramConfigurationError

    if getattr(settings, "ENABLE_TELEGRAM", False) and not getattr(settings, "TELEGRAM_DRY_RUN", True):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

        if not token or not chat_id:
             raise TelegramConfigurationError(
                 "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured when ENABLE_TELEGRAM is True and TELEGRAM_DRY_RUN is False."
             )
