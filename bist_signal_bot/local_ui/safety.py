from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUILayout, LocalUIPage, LocalUIShortcut, LocalUIStatus
import json

class LocalUISafetyGuard:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def validate_page(self, page: LocalUIPage) -> list[str]:
        findings = []
        findings.extend(self.detect_unsafe_text(page.title))
        for w in page.widgets:
            findings.extend(self.detect_unsafe_text(w.title))
            content_str = json.dumps(w.content, default=str)
            findings.extend(self.detect_unsafe_text(content_str))
        return list(set(findings))

    def validate_layout(self, layout: LocalUILayout) -> list[str]:
        findings = []
        for p in layout.pages:
            findings.extend(self.validate_page(p))
        return list(set(findings))

    def validate_shortcuts(self, shortcuts: list[LocalUIShortcut]) -> list[str]:
        findings = []
        for s in shortcuts:
            findings.extend(self.detect_unsafe_command(s.command))
            findings.extend(self.detect_unsafe_text(s.label))
        return list(set(findings))

    def detect_unsafe_text(self, text: str) -> list[str]:
        if not getattr(self.settings, "LOCAL_UI_SAFE_LANGUAGE_REQUIRED", True):
            return []

        unsafe_terms = [
            "garanti", "işlem yapılabilir", "trade ready", "live ready",
            "deployment approved", "broker ready", "hedef fiyat", "kesin al", "kesin sat"
        ]

        text_lower = text.lower()
        findings = []
        for term in unsafe_terms:
            if term in text_lower:
                findings.append(f"Unsafe term detected: {term}")

        return findings

    def detect_unsafe_command(self, command: str) -> list[str]:
        if not getattr(self.settings, "LOCAL_UI_BLOCK_UNSAFE_COMMANDS", True):
            return []

        unsafe_terms = [
            "broker", "live", "buy order", "sell order", "market order", "execute --live"
        ]

        cmd_lower = command.lower()
        findings = []
        for term in unsafe_terms:
            if term in cmd_lower:
                findings.append(f"Unsafe command term detected: {term}")

        if "--confirm" in cmd_lower and getattr(self.settings, "LOCAL_UI_BLOCK_WRITE_ACTIONS", True):
             findings.append("Command contains --confirm without proper validation")

        return findings

    def sanitize_text(self, text: str) -> str:
        if not getattr(self.settings, "LOCAL_UI_SECRET_REDACTION_ENABLED", True):
            return text

        import re
        text = re.sub(r'([A-Za-z0-9+/=]{40,})', '***REDACTED_SECRET***', text)
        return text

    def status_from_findings(self, findings: list[str]) -> LocalUIStatus:
        if not findings:
            return LocalUIStatus.PASS
        if any("Unsafe command" in f for f in findings):
            return LocalUIStatus.BLOCKED
        return LocalUIStatus.WATCH
