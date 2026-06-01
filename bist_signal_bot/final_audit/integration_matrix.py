from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.final_audit.models import (
    FinalIntegrationMatrix,
    FinalIntegrationMatrixItem,
    FinalAuditStatus
)
from bist_signal_bot.config.settings import Settings

class FinalIntegrationMatrixBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def build_matrix(self) -> FinalIntegrationMatrix:
        items = []
        for item in self.default_items():
            items.append(self.evaluate_item(item))

        failing_req = len(self.required_failures(items))
        blocked = sum(1 for i in items if i.latest_status == FinalAuditStatus.BLOCKED)

        return FinalIntegrationMatrix(
            matrix_id=f"int_{uuid.uuid4().hex[:8]}",
            created_at=datetime.now(timezone.utc),
            items=items,
            total_count=len(items),
            failing_required_count=failing_req,
            blocked_count=blocked,
            status=self.matrix_status(items)
        )

    def default_items(self) -> list[FinalIntegrationMatrixItem]:
        pairs = [
            ("bootstrap", "qa", "Bootstrap -> QA"),
            ("bootstrap", "ops", "Bootstrap -> Ops"),
            ("cli_ux", "qa", "CLI UX -> QA"),
            ("cli_ux", "docs_hub", "CLI UX -> Docs Hub"),
            ("docs_hub", "bootstrap", "Docs Hub -> Bootstrap"),
            ("data_catalog", "feature_store", "Data Catalog -> Feature Store"),
            ("data_catalog", "ops", "Data Catalog -> Ops"),
            ("feature_store", "scanner", "Feature Store -> Scanner"),
            ("feature_store", "validation", "Feature Store -> Validation"),
            ("feature_store", "model_registry", "Feature Store -> Model Registry"),
            ("model_registry", "ml", "Model Registry -> ML Inference"),
            ("model_registry", "context_fusion", "Model Registry -> Context Fusion"),
            ("monitoring", "model_registry", "Monitoring -> Model Registry"),
            ("monitoring", "leaderboard", "Monitoring -> Leaderboard"),
            ("leaderboard", "portfolio_construction", "Leaderboard -> Portfolio Construction"),
            ("leaderboard", "review_workflow", "Leaderboard -> Review Workflow"),
            ("research_orchestrator", "data_catalog", "Orchestrator -> Data Catalog"),
            ("research_orchestrator", "feature_store", "Orchestrator -> Feature Store"),
            ("research_orchestrator", "monitoring", "Orchestrator -> Monitoring"),
            ("research_orchestrator", "leaderboard", "Orchestrator -> Leaderboard"),
            ("qa", "ops", "QA -> Ops"),
            ("reports", "all_summary", "Reports -> all summary sections"),
        ]

        return [
            FinalIntegrationMatrixItem(
                item_id=f"pair_{idx}",
                source_module=src,
                target_module=tgt,
                integration_name=name,
                required=True,
                latest_status=FinalAuditStatus.UNKNOWN
            ) for idx, (src, tgt, name) in enumerate(pairs)
        ]

    def evaluate_item(self, item: FinalIntegrationMatrixItem) -> FinalIntegrationMatrixItem:
        # Mock evaluation
        item.latest_status = FinalAuditStatus.PASS
        return item

    def required_failures(self, items: list[FinalIntegrationMatrixItem]) -> list[FinalIntegrationMatrixItem]:
        return [i for i in items if i.required and i.latest_status in (FinalAuditStatus.FAIL, FinalAuditStatus.BLOCKED)]

    def matrix_status(self, items: list[FinalIntegrationMatrixItem]) -> FinalAuditStatus:
        if any(i.latest_status == FinalAuditStatus.BLOCKED for i in items):
            return FinalAuditStatus.BLOCKED
        if self.required_failures(items):
            return FinalAuditStatus.FAIL
        if any(i.latest_status == FinalAuditStatus.WATCH for i in items):
            return FinalAuditStatus.WATCH
        return FinalAuditStatus.PASS
