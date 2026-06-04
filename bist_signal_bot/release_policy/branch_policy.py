import re
import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.release_policy.models import (
    BranchPolicy, BranchKind, ChangeType, ChangeRequest
)

class BranchPolicyRegistry:
    def __init__(self) -> None:
        pass

    def default_branch_policies(self) -> List[BranchPolicy]:
        return [
            BranchPolicy(
                policy_id="main_branch_policy_v1",
                branch_kind=BranchKind.MAIN,
                name_pattern="^main$",
                allowed_change_types=[ChangeType.BUGFIX, ChangeType.DOCS],
                requires_qa=True,
                requires_ops=True,
                requires_final_audit=True,
                requires_changelog=True,
                requires_migration_notes=True,
                requires_compatibility_check=True,
                protected=True
            ),
            BranchPolicy(
                policy_id="develop_branch_policy_v1",
                branch_kind=BranchKind.DEVELOP,
                name_pattern="^develop$",
                allowed_change_types=[
                    ChangeType.FEATURE, ChangeType.BUGFIX, ChangeType.REFACTOR,
                    ChangeType.DOCS, ChangeType.TEST, ChangeType.CONFIG, ChangeType.SCHEMA,
                    ChangeType.CLI_CONTRACT, ChangeType.DATA_CONTRACT, ChangeType.SECURITY,
                    ChangeType.PERFORMANCE, ChangeType.DEPRECATION, ChangeType.MIGRATION,
                    ChangeType.CUSTOM
                ],
                requires_qa=False,
                requires_ops=False,
                requires_final_audit=False,
                requires_changelog=False,
                requires_migration_notes=False,
                requires_compatibility_check=True,
                protected=True
            ),
            BranchPolicy(
                policy_id="release_branch_policy_v1",
                branch_kind=BranchKind.RELEASE,
                name_pattern="^release/.*$",
                allowed_change_types=[ChangeType.BUGFIX, ChangeType.DOCS, ChangeType.TEST],
                requires_qa=True,
                requires_ops=True,
                requires_final_audit=True,
                requires_changelog=True,
                requires_migration_notes=True,
                requires_compatibility_check=True,
                protected=True
            ),
            BranchPolicy(
                policy_id="hotfix_branch_policy_v1",
                branch_kind=BranchKind.HOTFIX,
                name_pattern="^hotfix/.*$",
                allowed_change_types=[ChangeType.BUGFIX, ChangeType.SECURITY, ChangeType.DOCS],
                requires_qa=True,
                requires_ops=True,
                requires_final_audit=False,
                requires_changelog=True,
                requires_migration_notes=False,
                requires_compatibility_check=True,
                protected=False
            ),
            BranchPolicy(
                policy_id="feature_branch_policy_v1",
                branch_kind=BranchKind.FEATURE,
                name_pattern="^feature/.*$",
                allowed_change_types=[c for c in ChangeType if c != ChangeType.BREAKING],
                requires_qa=False,
                requires_ops=False,
                requires_final_audit=False,
                requires_changelog=False,
                requires_migration_notes=False,
                requires_compatibility_check=False,
                protected=False
            ),
            BranchPolicy(
                policy_id="experimental_branch_policy_v1",
                branch_kind=BranchKind.EXPERIMENTAL,
                name_pattern="^experimental/.*$",
                allowed_change_types=list(ChangeType),
                requires_qa=False,
                requires_ops=False,
                requires_final_audit=False,
                requires_changelog=False,
                requires_migration_notes=False,
                requires_compatibility_check=False,
                protected=False,
                warnings=["Experimental branch cannot produce release artifacts."]
            ),
            BranchPolicy(
                policy_id="archive_branch_policy_v1",
                branch_kind=BranchKind.ARCHIVE,
                name_pattern="^archive/.*$",
                allowed_change_types=[],
                requires_qa=False,
                requires_ops=False,
                requires_final_audit=False,
                requires_changelog=False,
                requires_migration_notes=False,
                requires_compatibility_check=False,
                protected=True
            )
        ]

    def policy_for_branch(self, branch_name: str) -> Optional[BranchPolicy]:
        for policy in self.default_branch_policies():
            if re.match(policy.name_pattern, branch_name):
                return policy
        return None

    def classify_branch(self, branch_name: str) -> BranchKind:
        policy = self.policy_for_branch(branch_name)
        if policy:
            return policy.branch_kind
        return BranchKind.UNKNOWN

    def validate_branch_policy(self, policy: BranchPolicy) -> List[str]:
        errors = []
        if policy.branch_kind == BranchKind.MAIN and not policy.protected:
            errors.append("main branch must be protected.")
        if policy.branch_kind == BranchKind.RELEASE:
            if not policy.requires_qa:
                errors.append("release branch must require QA.")
            if not policy.requires_ops:
                errors.append("release branch must require Ops.")
            if not policy.requires_final_audit:
                errors.append("release branch must require Final Audit.")
        return errors

    def validate_change_for_branch(self, change: ChangeRequest, branch_name: str) -> List[str]:
        policy = self.policy_for_branch(branch_name)
        errors = []
        if not policy:
            errors.append(f"No branch policy found for {branch_name}")
            return errors

        if change.change_type not in policy.allowed_change_types:
            errors.append(f"Change type {change.change_type} not allowed on {branch_name}")

        if policy.branch_kind == BranchKind.EXPERIMENTAL and change.change_type == ChangeType.BREAKING:
            errors.append("experimental branch cannot produce release artifacts.")

        if policy.branch_kind == BranchKind.RELEASE and change.change_type == ChangeType.BREAKING:
            if not change.requires_migration:
                errors.append("breaking change on release branch must require migration notes.")

        return errors

    def branch_policy_summary(self, policy: BranchPolicy) -> Dict[str, Any]:
        return {
            "policy_id": policy.policy_id,
            "branch_kind": policy.branch_kind.value,
            "protected": policy.protected,
            "allowed_changes": len(policy.allowed_change_types)
        }
