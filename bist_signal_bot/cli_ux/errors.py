import uuid
from typing import Optional
from bist_signal_bot.cli_ux.models import CLIErrorMessage
from bist_signal_bot.cli_ux.exit_codes import CLIExitCodeMapper

class CLIErrorNormalizer:
    def __init__(self, settings=None):
        self.settings = settings
        self.exit_mapper = CLIExitCodeMapper(settings)

    def normalize_exception(self, exc: Exception, command: Optional[str] = None) -> CLIErrorMessage:
        error_type = exc.__class__.__name__
        technical_msg = str(exc)
        user_msg = self.user_message_for_error(error_type)
        if not user_msg:
            user_msg = self.safe_error_text(technical_msg)

        suggested_fix = self.suggested_fix_for_error(error_type)
        docs_ref = self.docs_ref_for_error(error_type)
        exit_code = self.exit_mapper.code_for_exception(exc)

        return CLIErrorMessage(
            error_id=str(uuid.uuid4()),
            error_type=error_type,
            command=command,
            user_message=user_msg,
            technical_message=technical_msg,
            suggested_fix=suggested_fix,
            docs_ref=docs_ref,
            exit_code=exit_code
        )

    def user_message_for_error(self, error_type: str) -> Optional[str]:
        mapping = {
            "FileNotFoundError": "A required file is missing.",
            "ConfigValidationError": "Configuration is invalid.",
            "SafetyBlockedError": "The operation was blocked for safety reasons.",
            "ConfirmRequiredError": "This operation requires explicit confirmation.",
            "UnknownCommandError": "The command provided is not recognized.",
            "InvalidSymbolError": "The provided symbol is invalid.",
            "StaleStoreError": "The local data store is stale."
        }
        return mapping.get(error_type)

    def suggested_fix_for_error(self, error_type: str) -> Optional[str]:
        mapping = {
            "FileNotFoundError": "Check the file path and ensure the file exists.",
            "ConfigValidationError": "Review the configuration overrides.",
            "SafetyBlockedError": "Check governance policies or use --force if safe.",
            "ConfirmRequiredError": "Run the command again with --confirm.",
            "StaleStoreError": "Run a data import or freshness check."
        }
        return mapping.get(error_type)

    def docs_ref_for_error(self, error_type: str) -> Optional[str]:
        return "See docs/63_CLI_UX_AND_OUTPUT_CONTRACTS.md for details."

    def safe_error_text(self, text: str) -> str:
        # Very simple safety filter
        unsafe_words = ["token", "password", "secret", "key"]
        lower_text = text.lower()
        for word in unsafe_words:
            if word in lower_text:
                return "An error occurred. Details are hidden for security."
        return text
