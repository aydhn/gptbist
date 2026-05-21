import os
import re

filepath = "bist_signal_bot/config/settings.py"
with open(filepath, "r") as f:
    content = f.read()

if "REVIEW_DIR_NAME:" not in content:
    review_settings = """
    # Analyst Review
    ENABLE_ANALYST_REVIEW: bool = True
    REVIEW_DIR_NAME: str = "review"
    REVIEW_ADD_SCANNER_SIGNALS: bool = False
    REVIEW_ADD_ENSEMBLE_SIGNALS: bool = True
    REVIEW_ADD_HIGH_PRIORITY_SIGNALS: bool = True
    REVIEW_AUTO_CHECKLIST: bool = True
    REVIEW_REQUIRE_THESIS_FOR_APPROVAL: bool = True
    REVIEW_REQUIRE_CHECKLIST_PASS_FOR_APPROVAL: bool = True
    REVIEW_ALLOW_APPROVE_WITH_WARNINGS: bool = True
    REVIEW_BLOCK_APPROVE_ON_GOVERNANCE_CRITICAL: bool = True

    REVIEW_ITEM_VALIDITY_DAYS: int = 14
    REVIEW_EXPIRE_STALE_ITEMS: bool = True
    REVIEW_STALE_IN_REVIEW_DAYS: int = 7

    REVIEW_FOLLOWUP_ENABLED: bool = True
    REVIEW_DEFAULT_FOLLOWUP_DAYS: int = 3
    REVIEW_REQUIRE_CONFIRM_FOR_FOLLOWUP_CLEAR: bool = True

    REVIEW_REQUIRE_CONFIRM_FOR_DECISION_CHANGE: bool = False
    REVIEW_REQUIRE_CONFIRM_FOR_ARCHIVE: bool = True
    REVIEW_REQUIRE_CONFIRM_FOR_REOPEN: bool = True
    REVIEW_REQUIRE_CONFIRM_FOR_JOURNAL_LESSON: bool = False

    RUNTIME_ADD_SIGNALS_TO_REVIEW: bool = False
    RUNTIME_REVIEW_AUTO_CHECKLIST: bool = True

    SCANNER_ADD_TO_REVIEW: bool = False
    REPORT_INCLUDE_ANALYST_REVIEW: bool = True
    RESEARCH_AUTO_LOG_REVIEW: bool = False
"""

    # insert before the class closing or some marker
    # let's just use regex to insert into Settings
    content = re.sub(r'(class Settings\(BaseSettings\):.*?)(?=\n\n|\Z)', r'\1\n' + review_settings, content, flags=re.DOTALL)

    with open(filepath, "w") as f:
        f.write(content)
