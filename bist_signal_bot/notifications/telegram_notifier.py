from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """
    Abstract base class for notification systems.
    """

    @abstractmethod
    def send_message(self, message: str):
        """Send a text message."""
        raise NotImplementedError("send_message must be implemented.")

class TelegramNotifier(BaseNotifier):
    """
    Telegram implementation for notifications. Placeholder for Phase 1.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, message: str):
        """
        Send message via Telegram API.
        TODO: Implement real HTTP request in future phases.
        """
        # Placeholder for actual implementation
        print(f"[Telegram Mock] To {self.chat_id}: {message}")
