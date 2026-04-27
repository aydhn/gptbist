import json
import logging
from pathlib import Path
from typing import Any

from bist_signal_bot.config.secrets import mask_secret, sanitize_config_dict
from bist_signal_bot.config.settings import Settings

# For backward compatibility
mask_sensitive_value = mask_secret

def sanitize_for_logging(data: Any, mask_secrets: bool = True) -> Any:
    """Recursively sanitizes a dictionary or list, masking sensitive values."""
    if not mask_secrets:
        return data

    if isinstance(data, dict):
        return sanitize_config_dict(data)
    elif isinstance(data, list):
        return [sanitize_for_logging(item, mask_secrets) for item in data]
    elif isinstance(data, str) and "token" in data.lower():
         # Basic string check for simple string cases if it resembles a token
         pass
    return data

def setup_logging(settings: Settings) -> logging.Logger:
    """
    Sets up and returns a configured root/project logger.
    Avoids duplicate handlers.
    """
    logger = logging.getLogger("bist_signal_bot")

    # Avoid adding multiple handlers if already set up
    if not logger.handlers:
        level_name = settings.LOG_LEVEL.upper()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if settings.LOG_TO_FILE:
            from logging.handlers import RotatingFileHandler
            log_dir = Path(settings.LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / settings.LOG_FILE_NAME

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=settings.LOG_MAX_BYTES,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def get_logger(name: str | None = None) -> logging.Logger:
    """
    Returns a logger for the given name in the project namespace.
    """
    if name and not name.startswith("bist_signal_bot.") and name != "bist_signal_bot":
        name = f"bist_signal_bot.{name}"
    return logging.getLogger(name or "bist_signal_bot")

def safe_log_dict(logger: logging.Logger, level: int, message: str, data: Any, mask_secrets: bool = True):
    """Logs a sanitized dictionary."""
    sanitized_data = sanitize_for_logging(data, mask_secrets)
    if isinstance(sanitized_data, dict) or isinstance(sanitized_data, list):
         try:
             data_str = json.dumps(sanitized_data, ensure_ascii=False)
         except Exception:
             data_str = str(sanitized_data)
    else:
         data_str = str(sanitized_data)

    logger.log(level, f"{message}: {data_str}")

# For backward compatibility with existing usage like `logger = setup_logger(__name__)`
setup_logger = get_logger
