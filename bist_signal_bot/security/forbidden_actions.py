import re
from pathlib import Path
from typing import Any

from bist_signal_bot.security.models import ForbiddenActionFinding, ForbiddenActionType, SecurityLevel
from bist_signal_bot.core.exceptions import ForbiddenActionError

class ForbiddenActionGuard:
    """Enforces boundaries so that no real broker/order/destructive actions can be taken."""

    # Patterns indicating forbidden programmatic behavior in source
    FORBIDDEN_PATTERNS = {
        ForbiddenActionType.REAL_ORDER_SEND: [
            r'send_order', r'place_order', r'create_order', r'execute_trade', r'buy_market', r'sell_market', r'live_order'
        ],
        ForbiddenActionType.BROKER_API_CALL: [
            r'broker', r'api\.binance', r'api\.alpaca', r'ccxt\.'
        ],
        ForbiddenActionType.HTML_SCRAPING: [
            r'bs4', r'selenium', r'webdriver', r'scrapy', r'playwright', r'requests\.get\(.*html.*'
        ],
        ForbiddenActionType.PAID_API_CALL: [
            r'openai\.api_key', r'bloomberg'
        ]
    }

    @classmethod
    def assert_no_real_order_action(cls, action_name: str, metadata: dict[str, Any] | None = None) -> None:
        """Called at runtime before pseudo-order creation to ensure we're not sending a real order."""
        action_name_lower = action_name.lower()
        for p in cls.FORBIDDEN_PATTERNS[ForbiddenActionType.REAL_ORDER_SEND]:
            if re.search(p, action_name_lower):
                raise ForbiddenActionError(f"Forbidden action detected: Real order intent blocked for '{action_name}'.")

    @classmethod
    def assert_no_broker_api_usage(cls, url_or_module: str, metadata: dict[str, Any] | None = None) -> None:
        """Called before network operations to prevent broker interactions."""
        val = url_or_module.lower()
        for p in cls.FORBIDDEN_PATTERNS[ForbiddenActionType.BROKER_API_CALL]:
            if re.search(p, val):
                raise ForbiddenActionError(f"Forbidden action detected: Broker API usage blocked for '{url_or_module}'.")

    @classmethod
    def assert_no_html_scraping(cls, action_name: str, metadata: dict[str, Any] | None = None) -> None:
        """Called to prevent web scraping."""
        val = action_name.lower()
        for p in cls.FORBIDDEN_PATTERNS[ForbiddenActionType.HTML_SCRAPING]:
            if re.search(p, val):
                raise ForbiddenActionError(f"Forbidden action detected: HTML Scraping blocked for '{action_name}'.")

    @classmethod
    def assert_no_paid_api(cls, action_name: str, metadata: dict[str, Any] | None = None) -> None:
        val = action_name.lower()
        for p in cls.FORBIDDEN_PATTERNS[ForbiddenActionType.PAID_API_CALL]:
            if re.search(p, val):
                raise ForbiddenActionError(f"Forbidden action detected: Paid API usage blocked for '{action_name}'.")

    @classmethod
    def scan_source_text(cls, source_text: str, location: str = "unknown") -> list[ForbiddenActionFinding]:
        """Statically scans source code text for suspicious patterns."""
        findings = []
        for action_type, patterns in cls.FORBIDDEN_PATTERNS.items():
            for p in patterns:
                for match in re.finditer(p, source_text, re.IGNORECASE):
                    findings.append(ForbiddenActionFinding(
                        action_type=action_type,
                        location=location,
                        message=f"Found suspicious pattern '{match.group(0)}' matching {action_type.value}",
                        severity=SecurityLevel.MEDIUM
                    ))
        return findings
