import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringComponent, MetricType
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimeJobResult

class MetricsCollector:
    def __init__(self, storage: Optional[MonitoringStore] = None, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.storage = storage or MonitoringStore(self.settings)
        self.logger = logger or logging.getLogger(__name__)

    def record_metric(self, component: MonitoringComponent, name: str, value: Any, metric_type: MetricType, unit: str | None = None, tags: dict[str, str] | None = None, metadata: dict[str, Any] | None = None) -> MonitoringMetric:
        metric = MonitoringMetric(
            metric_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            component=component,
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
            metadata=metadata or {}
        )

        try:
            self.storage.append_metric(metric)
        except Exception as e:
            self.logger.error(f"Failed to save metric {name}: {e}")

        return metric

    def record_runtime_result(self, result: RuntimePipelineResult) -> List[MonitoringMetric]:
        metrics = []

        metrics.append(self.record_metric(
            component=MonitoringComponent.RUNTIME,
            name="runtime_elapsed_seconds",
            value=result.elapsed_seconds,
            metric_type=MetricType.TIMER,
            unit="seconds",
            tags={"run_id": result.run_id, "trigger": result.trigger.value}
        ))

        is_success = result.status.value in ["SUCCESS", "PARTIAL_SUCCESS"]
        metrics.append(self.record_metric(
            component=MonitoringComponent.RUNTIME,
            name="runtime_success",
            value=is_success,
            metric_type=MetricType.STATUS,
            tags={"run_id": result.run_id, "status": result.status.value}
        ))

        total_jobs = len(result.job_results)
        success_jobs = sum(1 for j in result.job_results if j.status.value == "SUCCESS")
        failed_jobs = sum(1 for j in result.job_results if j.status.value == "FAILED")

        metrics.append(self.record_metric(
            component=MonitoringComponent.RUNTIME,
            name="runtime_total_jobs",
            value=total_jobs,
            metric_type=MetricType.COUNTER,
            tags={"run_id": result.run_id}
        ))

        metrics.append(self.record_metric(
            component=MonitoringComponent.RUNTIME,
            name="runtime_success_jobs",
            value=success_jobs,
            metric_type=MetricType.COUNTER,
            tags={"run_id": result.run_id}
        ))

        metrics.append(self.record_metric(
            component=MonitoringComponent.RUNTIME,
            name="runtime_failed_jobs",
            value=failed_jobs,
            metric_type=MetricType.COUNTER,
            tags={"run_id": result.run_id}
        ))

        if result.scan_report_summary:
            metrics.append(self.record_metric(
                component=MonitoringComponent.SCANNER,
                name="scanner_processed_symbols",
                value=result.scan_report_summary.get("total_symbols", 0),
                metric_type=MetricType.COUNTER,
                tags={"run_id": result.run_id}
            ))
            metrics.append(self.record_metric(
                component=MonitoringComponent.SCANNER,
                name="scanner_passed_count",
                value=result.scan_report_summary.get("passed_count", 0),
                metric_type=MetricType.COUNTER,
                tags={"run_id": result.run_id}
            ))
            metrics.append(self.record_metric(
                component=MonitoringComponent.SCANNER,
                name="scanner_error_count",
                value=result.scan_report_summary.get("error_count", 0),
                metric_type=MetricType.COUNTER,
                tags={"run_id": result.run_id}
            ))

        if result.paper_result_summary:
            metrics.append(self.record_metric(
                component=MonitoringComponent.PAPER,
                name="paper_fills_count",
                value=result.paper_result_summary.get("fills_generated", 0),
                metric_type=MetricType.COUNTER,
                tags={"run_id": result.run_id}
            ))

        if result.output_files:
            metrics.append(self.record_metric(
                component=MonitoringComponent.STORAGE,
                name="output_files_count",
                value=len(result.output_files),
                metric_type=MetricType.COUNTER,
                tags={"run_id": result.run_id}
            ))

        return metrics

    def record_job_result(self, result: RuntimeJobResult) -> List[MonitoringMetric]:
        metrics = []

        component = MonitoringComponent.RUNTIME
        if "SCAN" in result.job_type.value:
            component = MonitoringComponent.SCANNER
        elif "PAPER" in result.job_type.value:
            component = MonitoringComponent.PAPER
        elif "TELEGRAM" in result.job_type.value:
            component = MonitoringComponent.TELEGRAM

        metrics.append(self.record_metric(
            component=component,
            name=f"job_elapsed_{result.job_type.value.lower()}",
            value=result.elapsed_seconds,
            metric_type=MetricType.TIMER,
            unit="seconds",
            tags={"job_type": result.job_type.value, "status": result.status.value}
        ))

        metrics.append(self.record_metric(
            component=component,
            name=f"job_success_{result.job_type.value.lower()}",
            value=result.status.value == "SUCCESS",
            metric_type=MetricType.STATUS,
            tags={"job_type": result.job_type.value}
        ))

        return metrics

    def aggregate_recent_metrics(self, metrics: List[MonitoringMetric], window_minutes: int) -> dict[str, Any]:
        if not metrics:
            return {}

        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [m for m in metrics if m.timestamp >= cutoff]

        return self.metric_summary(recent)

    def metric_summary(self, metrics: List[MonitoringMetric]) -> dict[str, Any]:
        summary = {
            "total_count": len(metrics),
            "counters": {},
            "timers": {"avg": {}, "max": {}},
            "statuses": {}
        }

        timers_data = {}

        for m in metrics:
            if m.metric_type == MetricType.COUNTER:
                summary["counters"][m.name] = summary["counters"].get(m.name, 0) + (m.value if isinstance(m.value, (int, float)) else 1)
            elif m.metric_type == MetricType.TIMER:
                if m.name not in timers_data:
                    timers_data[m.name] = []
                timers_data[m.name].append(m.value if isinstance(m.value, (int, float)) else 0.0)
            elif m.metric_type == MetricType.STATUS:
                if m.name not in summary["statuses"]:
                    summary["statuses"][m.name] = {"true": 0, "false": 0}
                if m.value is True:
                    summary["statuses"][m.name]["true"] += 1
                else:
                    summary["statuses"][m.name]["false"] += 1

        for name, values in timers_data.items():
            if values:
                summary["timers"]["avg"][name] = sum(values) / len(values)
                summary["timers"]["max"][name] = max(values)

        return summary
