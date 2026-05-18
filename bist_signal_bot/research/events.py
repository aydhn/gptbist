from datetime import datetime
import uuid
from typing import Any

from ..config.settings import Settings, get_settings
from .models import ResearchRun, ResearchRunType, ResearchRunStatus, ResearchLineageRef

class ResearchEventBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _create_run_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def generic_run(self, run_type: ResearchRunType, title: str, metrics: dict[str, Any], metadata: dict[str, Any]) -> ResearchRun:
        return ResearchRun(
            run_id=self._create_run_id("gen"),
            run_type=run_type,
            status=ResearchRunStatus.SUCCESS,
            title=title,
            metrics=metrics,
            started_at=datetime.utcnow(),
            metadata=metadata
        )

    def from_backtest_result(self, result: Any, title: str | None = None) -> ResearchRun:
        lineage = getattr(result, "data_lineage_checksum", None)
        data_source = getattr(result, "data_source", None)
        metadata = getattr(result, "metadata", {})
        if lineage:
            metadata["data_lineage_checksum"] = lineage
        if data_source:
            metadata["data_source"] = data_source
        # Assuming result has some common fields. Handle getattr gracefully
        symbol = getattr(result, "symbol", "UNKNOWN")
        strategy_name = getattr(result, "strategy_name", getattr(result, "strategy", "UNKNOWN"))
        metrics = getattr(result, "metrics", {})

        return ResearchRun(
            run_id=self._create_run_id("bt"),
            run_type=ResearchRunType.BACKTEST,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Backtest {symbol} {strategy_name}",
            strategy_name=strategy_name,
            symbols=[symbol] if symbol != "UNKNOWN" else [],
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_optimization_result(self, result: Any, title: str | None = None) -> ResearchRun:
        strategy_name = getattr(result, "strategy_name", "UNKNOWN")
        symbol = getattr(result, "symbol", "UNKNOWN")
        metrics = getattr(result, "best_metrics", {})
        return ResearchRun(
            run_id=self._create_run_id("opt"),
            run_type=ResearchRunType.OPTIMIZATION,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Optimization {symbol} {strategy_name}",
            strategy_name=strategy_name,
            symbols=[symbol] if symbol != "UNKNOWN" else [],
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_scan_report(self, report: Any, title: str | None = None) -> ResearchRun:
        metrics = {"total_scanned": getattr(report, "total_scanned", 0), "signals_found": getattr(report, "total_signals", 0)}
        return ResearchRun(
            run_id=self._create_run_id("scan"),
            run_type=ResearchRunType.SIGNAL_SCAN,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Scan Report",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_paper_run_result(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"total_trades": getattr(result, "total_trades", 0), "pnl": getattr(result, "total_pnl", 0.0)}
        return ResearchRun(
            run_id=self._create_run_id("pap"),
            run_type=ResearchRunType.PAPER_TRADING,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Paper Run",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_ml_train_result(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = getattr(result, "metrics", {})
        return ResearchRun(
            run_id=self._create_run_id("mlt"),
            run_type=ResearchRunType.ML_TRAINING,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"ML Training",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_ml_prediction_result(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"predictions": len(getattr(result, "predictions", []))}
        return ResearchRun(
            run_id=self._create_run_id("mlp"),
            run_type=ResearchRunType.ML_INFERENCE,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"ML Inference",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_regime_classification(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"regime": getattr(result, "regime", "UNKNOWN")}
        return ResearchRun(
            run_id=self._create_run_id("reg"),
            run_type=ResearchRunType.REGIME_ANALYSIS,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Regime Analysis",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_runtime_result(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"success": getattr(result, "success", False)}
        return ResearchRun(
            run_id=self._create_run_id("run"),
            run_type=ResearchRunType.RUNTIME_PIPELINE,
            status=ResearchRunStatus.SUCCESS if metrics["success"] else ResearchRunStatus.FAILED,
            title=title or f"Runtime Execution",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_adaptive_recommendation(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"recommendation_count": len(getattr(result, "recommendations", []))}
        return ResearchRun(
            run_id=self._create_run_id("ada"),
            run_type=ResearchRunType.ADAPTIVE_RECOMMENDATION,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Adaptive Recommendation",
            metrics=metrics,
            started_at=datetime.utcnow()
        )

    def from_monitoring_snapshot(self, result: Any, title: str | None = None) -> ResearchRun:
        metrics = {"alerts": getattr(result, "active_alerts", 0)}
        return ResearchRun(
            run_id=self._create_run_id("mon"),
            run_type=ResearchRunType.MONITORING_DIAGNOSTIC,
            status=ResearchRunStatus.SUCCESS,
            title=title or f"Monitoring Snapshot",
            metrics=metrics,
            started_at=datetime.utcnow()
        )
