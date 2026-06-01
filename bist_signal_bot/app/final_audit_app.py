from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.final_audit import (
    FinalAuditStore,
    FinalAuditCheckRunner,
    FinalAcceptanceSuiteRunner,
    FinalContractAuditor,
    FinalIntegrationMatrixBuilder,
    FinalSecurityAuditor,
    ReleaseCandidateBuilder,
    HardeningFreezeManager,
    GoNoGoEvaluator,
    FinalRiskRegisterBuilder
)

def create_final_audit_store(settings: Settings | None = None, base_dir: Path | None = None) -> FinalAuditStore:
    return FinalAuditStore(settings=settings or get_settings(), base_dir=base_dir)

def create_final_audit_check_runner(settings: Settings | None = None, base_dir: Path | None = None) -> FinalAuditCheckRunner:
    return FinalAuditCheckRunner(settings=settings or get_settings(), base_dir=base_dir)

def create_final_acceptance_suite_runner(settings: Settings | None = None, base_dir: Path | None = None) -> FinalAcceptanceSuiteRunner:
    return FinalAcceptanceSuiteRunner(settings=settings or get_settings(), base_dir=base_dir)

def create_final_contract_auditor(settings: Settings | None = None, base_dir: Path | None = None) -> FinalContractAuditor:
    return FinalContractAuditor(settings=settings or get_settings(), base_dir=base_dir)

def create_final_integration_matrix_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalIntegrationMatrixBuilder:
    return FinalIntegrationMatrixBuilder(settings=settings or get_settings(), base_dir=base_dir)

def create_final_security_auditor(settings: Settings | None = None, base_dir: Path | None = None) -> FinalSecurityAuditor:
    return FinalSecurityAuditor(settings=settings or get_settings(), base_dir=base_dir)

def create_release_candidate_builder(settings: Settings | None = None, base_dir: Path | None = None) -> ReleaseCandidateBuilder:
    return ReleaseCandidateBuilder(settings=settings or get_settings(), base_dir=base_dir)

def create_hardening_freeze_manager(settings: Settings | None = None, base_dir: Path | None = None) -> HardeningFreezeManager:
    return HardeningFreezeManager(settings=settings or get_settings(), base_dir=base_dir)

def create_go_no_go_evaluator(settings: Settings | None = None, base_dir: Path | None = None) -> GoNoGoEvaluator:
    return GoNoGoEvaluator(settings=settings or get_settings(), base_dir=base_dir)

def create_final_risk_register_builder(settings: Settings | None = None, base_dir: Path | None = None) -> FinalRiskRegisterBuilder:
    return FinalRiskRegisterBuilder(settings=settings or get_settings(), base_dir=base_dir)
