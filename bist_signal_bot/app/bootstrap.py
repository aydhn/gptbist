from bist_signal_bot.config.settings import settings
from bist_signal_bot.core.logging_setup import setup_logger, setup_logging
from bist_signal_bot.core.audit import AuditLogger
from bist_signal_bot.core.context import create_runtime_context, set_runtime_context
from bist_signal_bot.core.error_handler import ErrorHandler
from bist_signal_bot.storage.paths import ensure_directories_exist
from bist_signal_bot.notifications.telegram_notifier import TelegramNotifier
from bist_signal_bot.notifications.mock_notifier import MockNotifier

# Call setup_logging with settings first to configure the root/project logger
logger = setup_logging(settings)

def initialize_app():
    """
    Initializes application dependencies, directories, logging, and contexts.
    Returns initialized components: settings, context, audit_logger, error_handler, notifier
    """
    logger.info("Initializing BIST Signal Bot...")

    # 1. Ensure Directories
    ensure_directories_exist()
    logger.debug("Core directories verified/created.")

    # 2. Setup Runtime Context
    context = create_runtime_context(settings)
    set_runtime_context(context)
    logger.debug(f"Runtime context created with run_id: {context.run_id}")

    # 3. Setup Audit Logger
    audit_logger = AuditLogger(settings)
    audit_logger.log_app_start(run_id=context.run_id, metadata={"app_env": settings.APP_ENV})

    # 4. Setup Notifier
    notifier = None
    if settings.ENABLE_TELEGRAM:
        if settings.DRY_RUN:
             logger.info("Initializing MockNotifier for DRY RUN.")
             notifier = MockNotifier()
        else:
             logger.info("Initializing TelegramNotifier.")
             notifier = TelegramNotifier.from_settings(settings)

    # 5. Setup Error Handler
    error_handler = ErrorHandler(settings, notifier=notifier)

    logger.info("Initialization complete.")
    return settings, context, audit_logger, error_handler, notifier
