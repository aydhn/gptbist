from typing import List
import pandas as pd
from bist_signal_bot.corporate_actions.models import CorporateActionRecord
from bist_signal_bot.data.reconciliation import DataQualityIssue, DataIssueType, DataIssueSeverity

class CorporateActionValidator:
    def validate_action(self, action: CorporateActionRecord) -> List[DataQualityIssue]:
        issues = []
        if action.adjustment_factor is not None and (action.adjustment_factor < 0.1 or action.adjustment_factor > 10.0):
            issues.append(DataQualityIssue(
                issue_id=f"ext_{action.action_id}",
                symbol=action.symbol,
                issue_type=DataIssueType.UNKNOWN,
                severity=DataIssueSeverity.WARNING,
                message="Extreme adjustment factor detected"
            ))
        return issues

    def validate_actions(self, actions: List[CorporateActionRecord]) -> List[DataQualityIssue]:
        issues = []
        for a in actions:
            issues.extend(self.validate_action(a))
        issues.extend(self.detect_duplicate_actions(actions))
        issues.extend(self.detect_unrealistic_factors(actions))
        return issues

    def detect_duplicate_actions(self, actions: List[CorporateActionRecord]) -> List[DataQualityIssue]:
        return []

    def detect_unrealistic_factors(self, actions: List[CorporateActionRecord]) -> List[DataQualityIssue]:
        return []

    def validate_against_price_gaps(self, symbol: str, actions: List[CorporateActionRecord], price_df: pd.DataFrame) -> List[DataQualityIssue]:
        return []
