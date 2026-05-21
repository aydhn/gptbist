import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import GovernancePolicyError
from bist_signal_bot.governance.models import (
    GovernanceDomain,
    GovernancePolicy,
    GovernanceRule,
    GovernanceRuleType,
    GovernanceSeverity,
)

class GovernancePolicyManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def default_policy(self, settings: Settings | None = None) -> GovernancePolicy:
        cfg = settings or self.settings
        version = getattr(cfg, "GOVERNANCE_POLICY_VERSION", "1.0.0")

        rules = [
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="no_real_order_sent disclaimer required",
                domain=GovernanceDomain.RESEARCH_ONLY,
                rule_type=GovernanceRuleType.REQUIRED_DISCLAIMER,
                severity=GovernanceSeverity.HIGH,
                blocking=getattr(cfg, "GOVERNANCE_WARN_ON_MISSING_DISCLAIMER", True),
                description="All outputs must clearly state that no real order was sent.",
                expected_setting="No real order was sent.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="not_investment_advice disclaimer required",
                domain=GovernanceDomain.FINANCIAL_CLAIMS,
                rule_type=GovernanceRuleType.REQUIRED_DISCLAIMER,
                severity=GovernanceSeverity.HIGH,
                blocking=getattr(cfg, "GOVERNANCE_WARN_ON_MISSING_DISCLAIMER", True),
                description="All outputs must clearly state that it is not investment advice.",
                expected_setting="Not investment advice.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="block forbidden phrases",
                domain=GovernanceDomain.FINANCIAL_CLAIMS,
                rule_type=GovernanceRuleType.FORBIDDEN_PATTERN,
                severity=GovernanceSeverity.CRITICAL,
                blocking=True,
                pattern=r"(?i)\b(kesin al|kesin sat|garanti kazanç|risksiz kazanç|emir gönder|gerçek order|broker API ile al)\b",
                description="Outputs must not contain phrases that suggest guaranteed profit or real order execution.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="block broker API enabled settings",
                domain=GovernanceDomain.BROKER_API,
                rule_type=GovernanceRuleType.REQUIRED_SETTING,
                severity=GovernanceSeverity.CRITICAL,
                blocking=True,
                expected_setting="BROKER_API_ENABLED",
                expected_value=False,
                description="Broker API usage is strictly forbidden.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="block paid API enabled settings",
                domain=GovernanceDomain.PAID_SERVICES,
                rule_type=GovernanceRuleType.REQUIRED_SETTING,
                severity=GovernanceSeverity.HIGH,
                blocking=True,
                expected_setting="PAID_API_ENABLED",
                expected_value=False,
                description="Paid API usage is strictly forbidden.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="block HTML scraping settings",
                domain=GovernanceDomain.HTML_SCRAPING,
                rule_type=GovernanceRuleType.REQUIRED_SETTING,
                severity=GovernanceSeverity.HIGH,
                blocking=True,
                expected_setting="HTML_SCRAPING_ENABLED",
                expected_value=False,
                description="HTML scraping usage is strictly forbidden.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="secret scan on outputs",
                domain=GovernanceDomain.SECRET_HYGIENE,
                rule_type=GovernanceRuleType.SECRET_SCAN,
                severity=GovernanceSeverity.CRITICAL,
                blocking=True,
                description="No outputs may contain unmasked secrets, API keys, or tokens.",
            ),
            GovernanceRule(
                rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                name="policy update confirm required",
                domain=GovernanceDomain.RESEARCH_ONLY,
                rule_type=GovernanceRuleType.CONFIRM_REQUIRED,
                severity=GovernanceSeverity.MEDIUM,
                blocking=True,
                expected_setting="confirm",
                expected_value=True,
                description="Policy updates must require explicit confirmation.",
            )
        ]

        return GovernancePolicy(
            policy_id=f"pol_{uuid.uuid4().hex[:8]}",
            version=version,
            created_at=datetime.utcnow(),
            rules=rules,
            require_research_only=getattr(cfg, "GOVERNANCE_REQUIRE_RESEARCH_ONLY", True),
            block_real_order_language=getattr(cfg, "GOVERNANCE_BLOCK_REAL_ORDER_LANGUAGE", True),
            block_broker_api=getattr(cfg, "GOVERNANCE_BLOCK_BROKER_API", True),
            block_paid_services=getattr(cfg, "GOVERNANCE_BLOCK_PAID_SERVICES", True),
            block_html_scraping=getattr(cfg, "GOVERNANCE_BLOCK_HTML_SCRAPING", True),
            require_secret_redaction=getattr(cfg, "GOVERNANCE_REQUIRE_SECRET_REDACTION", True),
            require_confirm_for_policy_update=getattr(cfg, "GOVERNANCE_REQUIRE_CONFIRM_FOR_POLICY_UPDATE", True),
        )

    def validate_policy(self, policy: GovernancePolicy) -> None:
        if not policy.policy_id:
            raise GovernancePolicyError("Policy ID cannot be empty")
        if not policy.version:
            raise GovernancePolicyError("Policy version cannot be empty")
        # Ensure no secrets in policy
        for rule in policy.rules:
            if rule.expected_setting and any(s in rule.expected_setting.lower() for s in ["token", "secret", "password", "key"]):
                if rule.expected_value and isinstance(rule.expected_value, str) and len(rule.expected_value) > 4:
                    raise GovernancePolicyError("Policy rules cannot contain plaintext secrets")

    def load_policy(self, path: Path | None = None) -> GovernancePolicy:
        if path is None:
            # return default if no path provided
            return self.default_policy()
        if not path.exists():
            return self.default_policy()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GovernancePolicy(**data)
        except Exception as e:
            raise GovernancePolicyError(f"Failed to load policy from {path}: {e}")

    def save_policy(self, policy: GovernancePolicy, path: Path | None = None, confirm: bool = False) -> Path:
        if policy.require_confirm_for_policy_update and not confirm:
            raise GovernancePolicyError("Policy update requires explicit confirmation (--confirm)")

        self.validate_policy(policy)

        if path is None:
            from bist_signal_bot.storage.paths import get_governance_dir
            gov_dir = get_governance_dir(self.settings)
            policy_dir = gov_dir / "policy"
            policy_dir.mkdir(parents=True, exist_ok=True)
            path = policy_dir / "governance_policy.json"

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(policy.model_dump_json(indent=2))
            return path
        except Exception as e:
            raise GovernancePolicyError(f"Failed to save policy to {path}: {e}")
