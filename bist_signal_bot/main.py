import json
import sys

from bist_signal_bot.app.bootstrap import initialize_app
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger("bist_signal_bot.main")

def main():
    try:
        # Initialize dependencies
        settings, context, audit_logger, error_handler, notifier = initialize_app()
    except Exception as e:
        # We don't have error_handler yet if bootstrap fails
        logger.exception(f"Application failed to initialize: {e}")
        sys.exit(1)

    try:
        logger.info(f"Running healthcheck (run_id: {context.run_id})...")
        health_status = run_healthcheck()

        # Log healthcheck as audit event
        audit_logger.log_healthcheck(health_status, run_id=context.run_id)

        logger.info("Healthcheck Results:")
        print(json.dumps(health_status, indent=4, ensure_ascii=False))

        # Send startup notification if configured
        if settings.SEND_STARTUP_NOTIFICATION and notifier:
             try:
                 notifier.send_text(
                     title="Bot Started",
                     body=f"BIST Signal Bot is running.\nRun ID: {context.run_id}\nEnv: {settings.APP_ENV}"
                 )
             except Exception as notif_err:
                 error_handler.handle_exception(notif_err, context={"action": "send_startup_notification"}, notify=False)

        logger.info("Phase 8 initialization complete. Logging, Error Handling, and Audit Trail established.")
    except Exception as e:
        error_handler.handle_exception(e, context={"run_id": context.run_id})
        logger.error("Application execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
