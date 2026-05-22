import uuid
from bist_signal_bot.telegram_center.models import DigestRequest, DigestResult, DigestType
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.config.settings import Settings

class DigestOrchestrator:
    def __init__(self, store: TelegramCenterStore, client: TelegramClient, settings: Settings):
        self.store = store
        self.client = client
        self.settings = settings

    def build_digest(self, request: DigestRequest) -> DigestResult:
        result = DigestResult(
            digest_id=str(uuid.uuid4()),
            request=request,
            title=f"Digest {request.digest_type.value}",
            body="Digest body"
        )
        self.store.save_digest(result)
        return result

    def build_daily_digest(self, max_items: int = 10) -> DigestResult:
        req = DigestRequest(digest_type=DigestType.DAILY, max_items_per_section=max_items)
        return self.build_digest(req)

    def build_weekly_digest(self, max_items: int = 20) -> DigestResult:
        req = DigestRequest(digest_type=DigestType.WEEKLY, max_items_per_section=max_items)
        return self.build_digest(req)

    def send_digest(self, result: DigestResult, dry_run: bool = False) -> DigestResult:
        if result.request.send and not dry_run:
            self.client.send_message(result.body)
            result.sent = True
        return result

    def format_section(self, title: str, body: str) -> str:
        return f"{title}\n{body}"
