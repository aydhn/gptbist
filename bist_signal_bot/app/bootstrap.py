from bist_signal_bot.storage.paths import ensure_directories_exist
from bist_signal_bot.core.logging_setup import setup_logger

logger = setup_logger(__name__)

def initialize_app():
    """
    Initializes application dependencies, directories, etc.
    """
    logger.info("Initializing BIST Signal Bot...")
    ensure_directories_exist()
    logger.info("Core directories verified/created.")
