from pathlib import Path

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.governance.attestation import ComplianceAttestationBuilder
from bist_signal_bot.governance.audit_review import AuditReviewEngine
from bist_signal_bot.governance.evidence import EvidencePackBuilder
from bist_signal_bot.governance.gate import GovernanceGate
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.governance.rules import GovernanceRuleEvaluator
from bist_signal_bot.governance.storage import GovernanceStore

def create_governance_policy_manager(settings: Settings | None = None, base_dir: Path | None = None) -> GovernancePolicyManager:
    return GovernancePolicyManager(settings or get_settings())

def create_governance_rule_evaluator(settings: Settings | None = None) -> GovernanceRuleEvaluator:
    return GovernanceRuleEvaluator(settings or get_settings())

def create_audit_review_engine(settings: Settings | None = None, base_dir: Path | None = None) -> AuditReviewEngine:
    return AuditReviewEngine(
        policy_manager=create_governance_policy_manager(settings, base_dir),
        rule_evaluator=create_governance_rule_evaluator(settings),
        settings=settings or get_settings(),
        base_dir=base_dir
    )

def create_evidence_pack_builder(settings: Settings | None = None, base_dir: Path | None = None) -> EvidencePackBuilder:
    return EvidencePackBuilder(settings or get_settings(), base_dir)

def create_governance_gate(settings: Settings | None = None, base_dir: Path | None = None) -> GovernanceGate:
    return GovernanceGate(settings or get_settings(), base_dir)

def create_attestation_builder(settings: Settings | None = None) -> ComplianceAttestationBuilder:
    return ComplianceAttestationBuilder(settings or get_settings())

def create_governance_store(settings: Settings | None = None, base_dir: Path | None = None) -> GovernanceStore:
    return GovernanceStore(settings or get_settings(), base_dir)
