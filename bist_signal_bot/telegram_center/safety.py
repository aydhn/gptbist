import re
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandDecision, TelegramCommandType
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.forbidden_actions import ForbiddenActionGuard
from bist_signal_bot.security.claims_guard import UnsafeClaimGuard
from bist_signal_bot.security.redaction import SecretRedactor

class TelegramCommandSafetyGuard:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.forbidden_guard = ForbiddenActionGuard()
        self.claims_guard = UnsafeClaimGuard()
        self.redactor = SecretRedactor()

    def evaluate(self, command: TelegramCommand) -> tuple[TelegramCommandDecision, list[str]]:
        warnings = []

        if command.command_type == TelegramCommandType.UNKNOWN:
            return TelegramCommandDecision.BLOCK_UNKNOWN_COMMAND, ["Unknown command type"]

        forbidden_phrases = ['al', 'sat', 'emir gönder', 'order', 'pozisyon aç', 'pozisyon kapat', 'broker', 'gerçek işlem', 'kaldıraç aç']

        text_lower = command.raw_text.lower()
        for phrase in forbidden_phrases:
            if phrase in text_lower:
                return TelegramCommandDecision.BLOCK_FORBIDDEN_ACTION, [f"Forbidden phrase detected: {phrase}"]

        # Shell injection check
        if any(char in command.raw_text for char in [';', '|', '&&', '||', '`', '$(']):
            return TelegramCommandDecision.BLOCK_UNSAFE_TEXT, ["Potential shell injection detected"]

        # Unsafe claim check
        if hasattr(self.claims_guard, 'evaluate_claims'):
            try:
                self.claims_guard.validate_text(command.raw_text)
            except Exception:
                return TelegramCommandDecision.BLOCK_UNSAFE_TEXT, ["Unsafe claim detected in input"]
                return TelegramCommandDecision.BLOCK_UNSAFE_TEXT, ["Unsafe claim detected in input"]

        return TelegramCommandDecision.ALLOW, warnings

    def sanitize_response(self, text: str) -> str:
        if getattr(self.settings, 'TELEGRAM_REDACT_OUTPUTS', True):
            text = self.redactor.redact(text)

        if hasattr(self.claims_guard, 'sanitize_text'):
            text = self.claims_guard.sanitize_text(text)

        return text

    def ensure_disclaimer(self, text: str) -> str:
        if not getattr(self.settings, 'TELEGRAM_APPEND_DISCLAIMER', True):
            return text

        disclaimer = "Telegram command result is research-only. Not investment advice. No real order was sent."
        if disclaimer not in text:
            return f"{text}\n\n{disclaimer}"
        return text

    def chunk_message(self, text: str, max_chars: int = 3500) -> list[str]:
        if not max_chars or max_chars <= 0:
            max_chars = 3500

        if len(text) <= max_chars:
            return [text]

        chunks = []
        lines = text.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk)

                if len(line) > max_chars:
                    # Line itself is too long, must split by chars
                    for i in range(0, len(line), max_chars):
                        chunks.append(line[i:i+max_chars])
                    current_chunk = ""
                else:
                    current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
