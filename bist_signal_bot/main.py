import json

from bist_signal_bot.app.bootstrap import initialize_app
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.core.logging_setup import setup_logger

logger = setup_logger("bist_signal_bot.main")

def main():
    try:
        initialize_app()
        logger.info("Application initialized successfully.")

        health_status = run_healthcheck()
        logger.info("Healthcheck Results:")
        print(json.dumps(health_status, indent=4, ensure_ascii=False))

        logger.info("Phase 1 initialization complete. Ready for future phases.")
    except Exception as e:
        logger.exception(f"Application failed to start: {e}")
        raise

if __name__ == "__main__":
    main()
