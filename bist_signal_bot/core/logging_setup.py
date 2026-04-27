import logging

from bist_signal_bot.config.settings import settings


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Sets up and returns a configured logger.
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if already set up
    if not logger.handlers:
        level_name = settings.LOG_LEVEL.upper()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
