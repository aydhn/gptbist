import pytest
from bist_signal_bot.security.forbidden_actions import ForbiddenActionGuard, ForbiddenActionType
from bist_signal_bot.core.exceptions import ForbiddenActionError

def test_forbidden_action_guard_real_order_action():
    with pytest.raises(ForbiddenActionError):
        ForbiddenActionGuard.assert_no_real_order_action("execute_buy_market_order")

    # Safe action should pass
    ForbiddenActionGuard.assert_no_real_order_action("calculate_paper_cost")

def test_forbidden_action_guard_broker_api_usage():
    with pytest.raises(ForbiddenActionError):
        ForbiddenActionGuard.assert_no_broker_api_usage("api.binance.com")

    # Safe URL should pass
    ForbiddenActionGuard.assert_no_broker_api_usage("local_cache_db")

def test_forbidden_action_guard_source_scan_suspicious_pattern():
    source_code = """
    def my_strategy():
        if price > 100:
            send_order("BUY")
    """
    findings = ForbiddenActionGuard.scan_source_text(source_code)
    assert len(findings) > 0
    assert findings[0].action_type == ForbiddenActionType.REAL_ORDER_SEND

def test_forbidden_action_guard_html_scraping():
    with pytest.raises(ForbiddenActionError):
        ForbiddenActionGuard.assert_no_html_scraping("import bs4")

    ForbiddenActionGuard.assert_no_html_scraping("import pandas")
