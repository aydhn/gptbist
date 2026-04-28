from dataclasses import dataclass

from bist_signal_bot.calendar.session import BistMarketSessionService
from bist_signal_bot.config.env_loader import load_env_file

# Load .env file first, before settings are imported
load_env_file()

from bist_signal_bot.config.secrets import settings_safe_dump, validate_telegram_secrets
from bist_signal_bot.config.settings import Settings, settings
from bist_signal_bot.core.audit import AuditLogger
from bist_signal_bot.core.context import RuntimeContext, create_runtime_context, set_runtime_context
from bist_signal_bot.core.error_handler import ErrorHandler
from bist_signal_bot.core.exceptions import ConfigurationError
from bist_signal_bot.core.logging_setup import setup_logging
from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS, SymbolUniverse
from bist_signal_bot.notifications.mock_notifier import MockNotifier
from bist_signal_bot.notifications.telegram_notifier import TelegramNotifier
from bist_signal_bot.storage.local_store import LocalMarketDataStore
from bist_signal_bot.storage.paths import ensure_directories_exist

# Call setup_logging with settings first to configure the root/project logger
logger = setup_logging(settings)

@dataclass
class ApplicationContext:
    settings: Settings
    runtime_context: RuntimeContext
    audit_logger: AuditLogger
    error_handler: ErrorHandler
    notifier: TelegramNotifier | MockNotifier | None
    symbol_universe: SymbolUniverse
    session_service: BistMarketSessionService
    local_store: LocalMarketDataStore

def bootstrap_app() -> ApplicationContext:
    """
    Initializes application dependencies, directories, logging, and contexts.
    Returns an ApplicationContext containing initialized components.
    """
    try:
        # Re-validate Telegram just in case
        validate_telegram_secrets(settings)
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e.message}")
        import sys
        sys.exit(1)

    logger.info("Initializing BIST Signal Bot...")
    logger.info(f"Loaded Settings Summary: {settings_safe_dump(settings)}")

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
        if settings.TELEGRAM_DRY_RUN:
             logger.info("Initializing MockNotifier for DRY RUN.")
             notifier = MockNotifier()
        else:
             logger.info("Initializing TelegramNotifier.")
             notifier = TelegramNotifier.from_settings(settings)

    # 5. Setup Error Handler
    error_handler = ErrorHandler(settings, notifier=notifier)

    # 6. Core Services
    universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
    session_service = BistMarketSessionService.from_settings(settings)
    local_store = LocalMarketDataStore(settings=settings)

    logger.info("Initialization complete.")
    return ApplicationContext(
        settings=settings,
        runtime_context=context,
        audit_logger=audit_logger,
        error_handler=error_handler,
        notifier=notifier,
        symbol_universe=universe,
        session_service=session_service,
        local_store=local_store
    )

# Maintain backward compatibility if needed, though we will update main.py
def initialize_app():
    ctx = bootstrap_app()
    return ctx.settings, ctx.runtime_context, ctx.audit_logger, ctx.error_handler, ctx.notifier
