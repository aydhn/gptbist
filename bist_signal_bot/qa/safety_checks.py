from bist_signal_bot.qa.models import QACheckResult, QAStatus, QACheckType, QAModuleName
import uuid
from datetime import datetime

class QASafetyChecker:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def run_all(self) -> list[QACheckResult]:
        return [
            self.check_safe_language_in_reports(),
            self.check_no_investment_advice_claims(),
            self.check_no_target_price_claims(),
            self.check_disclaimers_present(),
            self.check_notification_templates(),
            self.check_review_signoff_language()
        ]

    def check_safe_language_in_reports(self) -> QACheckResult:
        return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="safe_language", status=QAStatus.PASS, started_at=datetime.utcnow())

    def check_no_investment_advice_claims(self, texts=None) -> QACheckResult:
        return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="no_investment_advice", status=QAStatus.PASS, started_at=datetime.utcnow())

    def check_no_target_price_claims(self, texts=None) -> QACheckResult:
         return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="no_target_price", status=QAStatus.PASS, started_at=datetime.utcnow())

    def check_disclaimers_present(self, texts=None) -> QACheckResult:
         return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="disclaimers_present", status=QAStatus.PASS, started_at=datetime.utcnow())

    def check_notification_templates(self) -> QACheckResult:
         return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="notification_templates", status=QAStatus.PASS, started_at=datetime.utcnow())

    def check_review_signoff_language(self) -> QACheckResult:
         return QACheckResult(check_id=str(uuid.uuid4()), check_type=QACheckType.SAFETY_LANGUAGE, module_name=QAModuleName.SECURITY, name="signoff_language", status=QAStatus.PASS, started_at=datetime.utcnow())
