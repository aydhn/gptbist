import uuid
from typing import Any, Dict, List
from bist_signal_bot.release_policy.models import (
    ChangeRequest, ChangeType, ChangeRiskLevel, VersionBumpType, ReleasePolicyStatus
)

class ChangeControlManager:
    def __init__(self) -> None:
        pass

    def create_change_request(self, title: str, description: str, change_type: ChangeType, affected_modules: List[str], risk_level: ChangeRiskLevel = ChangeRiskLevel.MEDIUM) -> ChangeRequest:
        req_migration = change_type in [ChangeType.BREAKING, ChangeType.SCHEMA, ChangeType.CLI_CONTRACT, ChangeType.DATA_CONTRACT]
        req_deprecation = change_type == ChangeType.DEPRECATION
        req_docs = change_type in [ChangeType.FEATURE, ChangeType.BREAKING, ChangeType.DOCS]
        req_tests = change_type not in [ChangeType.DOCS]

        bump = VersionBumpType.NONE
        if change_type == ChangeType.BREAKING:
            bump = VersionBumpType.MAJOR
        elif change_type in [ChangeType.FEATURE, ChangeType.DEPRECATION]:
            bump = VersionBumpType.MINOR
        elif change_type in [ChangeType.BUGFIX, ChangeType.SECURITY, ChangeType.PERFORMANCE]:
            bump = VersionBumpType.PATCH

        return ChangeRequest(
            change_id=str(uuid.uuid4()),
            title=title,
            description=description,
            change_type=change_type,
            risk_level=risk_level,
            affected_modules=affected_modules,
            proposed_version_bump=bump,
            requires_migration=req_migration,
            requires_deprecation_notice=req_deprecation,
            requires_docs_update=req_docs,
            requires_tests_update=req_tests,
            status=ReleasePolicyStatus.DRAFT
        )

    def classify_change(self, description: str, affected_modules: List[str]) -> ChangeType:
        d = description.lower()
        if "break" in d: return ChangeType.BREAKING
        if "fix" in d: return ChangeType.BUGFIX
        if "sec" in d or "vuln" in d: return ChangeType.SECURITY
        if "feat" in d or "add" in d: return ChangeType.FEATURE
        if "schema" in d: return ChangeType.SCHEMA
        return ChangeType.CUSTOM

    def estimate_risk(self, change_type: ChangeType, affected_modules: List[str]) -> ChangeRiskLevel:
        if change_type in [ChangeType.SECURITY, ChangeType.BREAKING]:
            return ChangeRiskLevel.CRITICAL
        if change_type in [ChangeType.SCHEMA, ChangeType.DATA_CONTRACT]:
            return ChangeRiskLevel.HIGH
        if change_type in [ChangeType.DOCS, ChangeType.TEST]:
            return ChangeRiskLevel.LOW
        return ChangeRiskLevel.MEDIUM

    def required_artifacts(self, change: ChangeRequest) -> Dict[str, bool]:
        return {
            "migration_notes": change.requires_migration,
            "deprecation_notice": change.requires_deprecation_notice,
            "changelog": True,
            "docs": change.requires_docs_update,
            "tests": change.requires_tests_update
        }

    def validate_change_request(self, change: ChangeRequest) -> List[str]:
        errors = []
        if change.change_type == ChangeType.BREAKING and not change.requires_migration:
            errors.append("Breaking change must require migration notes.")
        if change.risk_level == ChangeRiskLevel.CRITICAL and change.change_type not in [ChangeType.SECURITY, ChangeType.BREAKING]:
             pass
        return errors

    def change_summary(self, change: ChangeRequest) -> Dict[str, Any]:
        return {
            "id": change.change_id,
            "title": change.title,
            "type": change.change_type.value,
            "risk": change.risk_level.value,
            "status": change.status.value
        }
