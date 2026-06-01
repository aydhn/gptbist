from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.final_audit.models import (
    FinalRiskRegisterItem,
    ReleaseCandidateManifest,
    FinalAuditStatus
)
from bist_signal_bot.config.settings import Settings

class FinalRiskRegisterBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def build_risk_register(self, candidate: ReleaseCandidateManifest | None = None) -> list[FinalRiskRegisterItem]:
        items = self.default_known_risks()
        if candidate and candidate.warnings:
            items.extend(self.risks_from_warnings(candidate.warnings))
        return items

    def risks_from_warnings(self, warnings: list[str]) -> list[FinalRiskRegisterItem]:
        return [
            FinalRiskRegisterItem(
                risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                title="Warning Risk",
                description=w,
                severity=self.classify_risk("Warning", w),
                status=FinalAuditStatus.WATCH,
                accepted=False
            ) for w in warnings
        ]

    def default_known_risks(self) -> list[FinalRiskRegisterItem]:
        risks = [
            ("Local data quality dependency", "Systems relies on local data imports; data quality affects outcomes."),
            ("Synthetic demo limitation", "Demo scenarios might not capture extreme market conditions."),
            ("No broker/live execution by design", "Missing live feedback loops."),
            ("Model validation may be sample-limited", "Backtesting over limited history may overfit."),
            ("Feature drift requires periodic review", "Features may degrade in predictive power."),
            ("Docs may lag code if not regenerated", "Potential drift between docs and code."),
            ("CLI contract drift possible after future changes", "CLI updates may break downstream automated parsers.")
        ]

        return [
            FinalRiskRegisterItem(
                risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                title=t,
                description=d,
                severity="MEDIUM",
                status=FinalAuditStatus.PASS,
                accepted=True
            ) for t, d in risks
        ]

    def classify_risk(self, title: str, description: str) -> str:
        text = (title + " " + description).lower()
        if "critical" in text or "blocked" in text or "fail" in text:
            return "HIGH"
        return "MEDIUM"

    def validate_risk_register(self, items: list[FinalRiskRegisterItem]) -> list[str]:
        errors = []
        for i in items:
            if not i.title or not i.description:
                errors.append(f"Risk {i.risk_id} missing title or description.")
        return errors
