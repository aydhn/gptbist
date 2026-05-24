import pandas as pd
from typing import List, Optional
from datetime import datetime
from bist_signal_bot.data.reconciliation import DataReconciliationResult, DataQualityIssue, DataIssueType, DataIssueSeverity
from bist_signal_bot.corporate_actions.models import CorporateActionRecord

class DataReconciliationEngine:
    def compare_providers(self, symbol: str, df_a: pd.DataFrame, df_b: pd.DataFrame, provider_a: str, provider_b: str) -> DataReconciliationResult:
        mismatches = 0
        if not df_a.empty and not df_b.empty:
            common = df_a.index.intersection(df_b.index)
            if len(common) > 0:
                diff = (df_a.loc[common, 'Close'] - df_b.loc[common, 'Close']).abs()
                mismatches = len(diff[diff > 0.01])

        return DataReconciliationResult(
            reconciliation_id=f"rec_{symbol}",
            symbol=symbol,
            provider_a=provider_a,
            provider_b=provider_b,
            rows_compared=len(df_a),
            mismatches=mismatches
        )

    def detect_price_mismatches(self, symbol: str, df_a: pd.DataFrame, df_b: pd.DataFrame) -> List[DataQualityIssue]:
        return []

    def detect_volume_mismatches(self, symbol: str, df_a: pd.DataFrame, df_b: pd.DataFrame) -> List[DataQualityIssue]:
        return []

    def detect_missing_bars(self, df: pd.DataFrame, expected_calendar: List[datetime]) -> List[DataQualityIssue]:
        return []

    def detect_duplicate_bars(self, df: pd.DataFrame) -> List[DataQualityIssue]:
        issues = []
        if df.index.duplicated().any():
             issues.append(DataQualityIssue(
                 issue_id="dup_idx",
                 symbol="TEST",
                 issue_type=DataIssueType.DUPLICATE_BAR,
                 severity=DataIssueSeverity.HIGH,
                 message="Duplicate index found"
             ))
        return issues

    def detect_invalid_prices(self, df: pd.DataFrame) -> List[DataQualityIssue]:
        issues = []
        if 'Close' in df.columns and (df['Close'] <= 0).any():
             issues.append(DataQualityIssue(
                 issue_id="zero_price",
                 symbol="TEST",
                 issue_type=DataIssueType.ZERO_PRICE,
                 severity=DataIssueSeverity.HIGH,
                 message="Zero or negative price found"
             ))
        return issues

    def detect_abnormal_gaps(self, symbol: str, df: pd.DataFrame, actions: Optional[List[CorporateActionRecord]] = None) -> List[DataQualityIssue]:
        return []
