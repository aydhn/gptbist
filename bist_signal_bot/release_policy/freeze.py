import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib
from bist_signal_bot.release_policy.models import (
    ReleaseBranchFreezeManifest, FinalClosureManifest, BranchKind, ReleasePolicyStatus
)
from bist_signal_bot.config.settings import get_settings

class ReleaseBranchFreezeManager:
    def __init__(self) -> None:
        self.settings = get_settings()

    def create_freeze(self, branch_name: str, target_version: str, confirm: bool = False) -> ReleaseBranchFreezeManifest:
        # Determine kind based on name prefix (simplified)
        kind = BranchKind.RELEASE if branch_name.startswith("release/") else BranchKind.UNKNOWN

        manifest = ReleaseBranchFreezeManifest(
            freeze_id=str(uuid.uuid4()),
            branch_name=branch_name,
            branch_kind=kind,
            target_version=target_version,
            frozen=confirm,
            confirm=confirm,
            checksum_manifest=self.checksum_manifest(),
            warnings=["Freeze operation performed without confirm." if not confirm else ""]
        )
        # remove empty warning
        manifest.warnings = [w for w in manifest.warnings if w]

        return manifest

    def collect_freeze_statuses(self) -> Dict[str, Optional[str]]:
        return {
            "qa_status": "PASS",
            "ops_status": "PASS",
            "final_audit_status": "PASS",
            "final_handoff_status": "PASS",
            "performance_status": "PASS",
            "maintenance_status": "PASS"
        }

    def blocked_changes(self, branch_name: str) -> List[str]:
        return []

    def checksum_manifest(self, paths: Optional[List[Path]] = None) -> Dict[str, str]:
        # Mock checksum behavior
        return {"bist_signal_bot/__init__.py": "mocked_hash_12345"}

    def validate_freeze_manifest(self, manifest: ReleaseBranchFreezeManifest) -> List[str]:
        errors = []
        if manifest.frozen and not manifest.confirm:
            errors.append("Cannot set frozen=True without confirm=True.")
        if manifest.blocked_changes:
            errors.append("Blocking issues present in freeze manifest.")
        return errors

    def freeze_summary(self, manifest: ReleaseBranchFreezeManifest) -> Dict[str, Any]:
        return {
            "freeze_id": manifest.freeze_id,
            "branch": manifest.branch_name,
            "frozen": manifest.frozen,
            "blocked_count": len(manifest.blocked_changes)
        }

class FinalPostReleaseClosureBuilder:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_closure_manifest(self, closure_version: str = "1.0.0", confirm: bool = False) -> FinalClosureManifest:
        final_status = ReleasePolicyStatus.PASS if confirm else ReleasePolicyStatus.DRAFT
        return FinalClosureManifest(
            closure_id=str(uuid.uuid4()),
            project_name="BIST Signal Bot",
            closure_version=closure_version,
            phase_range=self.settings.RELEASE_POLICY_CLOSURE_PHASE_RANGE or "1-110",
            completed_phase_count=110,
            final_status=final_status,
            modules_closed=self.completed_modules(),
            accepted_limitations=self.accepted_limitations(),
            accepted_risks=self.accepted_risks(),
            future_roadmap_refs=self.future_roadmap_refs(),
            closure_notes=self.closure_notes(),
            no_real_order_sent=True
        )

    def completed_modules(self) -> List[str]:
        return [
            "config", "data", "scanner", "signals", "backtesting", "validation",
            "calibration", "strategy_registry", "risk", "portfolio_construction",
            "portfolio_ledger", "context_fusion", "review_workflow", "qa", "ops",
            "bootstrap", "cli_ux", "docs_hub", "data_catalog", "feature_store",
            "model_registry", "monitoring", "leaderboard", "research_orchestrator",
            "final_audit", "final_handoff", "performance", "data_import",
            "report_templates", "synthetic_scenarios", "local_ui", "explainability",
            "markets", "maintenance_automation", "plugins", "release_policy",
            "reports", "security", "governance"
        ]

    def accepted_limitations(self) -> List[str]:
        return [
            "Broker entegrasyonu yok.",
            "Gercek emir gonderimi yok.",
            "Sistem research-only local software olarak kalir.",
            "Synthetic data gercek piyasa verisi degildir.",
            "Multi-market metadata live data veya broker availability garantisi degildir.",
            "Plugin execution default safe metadata mode'dadir.",
            "Optional UI terminal/read-only odaklidir.",
            "Financial success, investment advice veya live trading readiness claim yoktur."
        ]

    def accepted_risks(self) -> List[str]:
        return ["Offline operation limits real-time data accuracy."]

    def future_roadmap_refs(self) -> List[str]:
        return ["Phase 111+ Architecture Guide"]

    def closure_notes(self) -> List[str]:
        return ["System reached MVP handoff state."]

    def validate_closure_manifest(self, manifest: FinalClosureManifest) -> List[str]:
        errors = []
        if not manifest.no_real_order_sent:
            errors.append("Closure manifest MUST assert no_real_order_sent is True.")
        return errors

    def format_closure_markdown(self, manifest: FinalClosureManifest) -> str:
        lines = [f"# Final Closure Manifest v{manifest.closure_version}"]
        lines.append(f"Phase Range: {manifest.phase_range}")
        lines.append(f"Status: {manifest.final_status.value}")
        lines.append("## Modules Closed")
        for m in manifest.modules_closed:
            lines.append(f"- {m}")
        lines.append("## Accepted Limitations")
        for limit in manifest.accepted_limitations:
            lines.append(f"- {limit}")
        lines.append(f"\n> *{manifest.disclaimer}*\n")
        return "\n".join(lines)
