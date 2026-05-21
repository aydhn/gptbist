import logging
import pandas as pd
import numpy as np
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    FeatureDriftResult, DriftMetric, DriftTestType, DriftDomain,
    DriftStatus, DriftSeverity
)
from bist_signal_bot.drift.statistics import DriftStatistics

logger = logging.getLogger(__name__)

class FeatureDriftDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def detect(self, reference_df: pd.DataFrame, current_df: pd.DataFrame, feature_names: list[str] | None = None) -> list[FeatureDriftResult]:
        if feature_names is None:
            feature_names = list(set(reference_df.columns).intersection(set(current_df.columns)))

        results = []
        for feature in feature_names:
            if feature not in reference_df.columns or feature not in current_df.columns:
                res = FeatureDriftResult(
                    feature_name=feature,
                    status=DriftStatus.ERROR,
                    severity=DriftSeverity.UNKNOWN,
                    warnings=[f"Feature '{feature}' missing from reference or current data"]
                )
                results.append(res)
                continue

            ref_series = reference_df[feature]
            cur_series = current_df[feature]

            if pd.api.types.is_numeric_dtype(ref_series):
                result = self.detect_numeric_feature(feature, ref_series, cur_series)
            else:
                result = self.detect_categorical_feature(feature, ref_series, cur_series)

            results.append(result)

        return results

    def detect_numeric_feature(self, feature_name: str, reference: pd.Series, current: pd.Series) -> FeatureDriftResult:
        ref_vals = reference.dropna().tolist()
        cur_vals = current.dropna().tolist()

        ref_count = len(ref_vals)
        cur_count = len(cur_vals)

        result = FeatureDriftResult(
            feature_name=feature_name,
            reference_summary=self.feature_summary(reference),
            current_summary=self.feature_summary(current)
        )

        if ref_count < self.settings.DRIFT_MIN_SAMPLES or cur_count < self.settings.DRIFT_MIN_SAMPLES:
            result.status = DriftStatus.INSUFFICIENT_DATA
            result.severity = DriftSeverity.LOW
            result.warnings.append(f"Insufficient samples (Ref: {ref_count}, Cur: {cur_count}). Minimum required: {self.settings.DRIFT_MIN_SAMPLES}")
            return result

        metrics = []

        psi_val = DriftStatistics.population_stability_index(ref_vals, cur_vals)
        psi_status = DriftStatus.STABLE
        psi_severity = DriftSeverity.LOW

        if psi_val is not None:
            if psi_val >= self.settings.DRIFT_FEATURE_PSI_SEVERE:
                psi_status = DriftStatus.SEVERE_DRIFT
                psi_severity = DriftSeverity.CRITICAL
            elif psi_val >= self.settings.DRIFT_FEATURE_PSI_FAIL:
                psi_status = DriftStatus.DRIFTING
                psi_severity = DriftSeverity.HIGH
            elif psi_val >= self.settings.DRIFT_FEATURE_PSI_WARN:
                psi_status = DriftStatus.WATCH
                psi_severity = DriftSeverity.MEDIUM

        metrics.append(DriftMetric(
            metric_name="psi",
            test_type=DriftTestType.PSI,
            domain=DriftDomain.FEATURE,
            value=psi_val,
            threshold_warn=self.settings.DRIFT_FEATURE_PSI_WARN,
            threshold_fail=self.settings.DRIFT_FEATURE_PSI_FAIL,
            status=psi_status,
            severity=psi_severity,
            sample_count_reference=ref_count,
            sample_count_current=cur_count
        ))

        ks_val = DriftStatistics.ks_statistic(ref_vals, cur_vals)
        ks_status = DriftStatus.STABLE
        ks_severity = DriftSeverity.LOW

        if ks_val is not None:
            if ks_val >= self.settings.DRIFT_FEATURE_KS_FAIL:
                ks_status = DriftStatus.DRIFTING
                ks_severity = DriftSeverity.HIGH
            elif ks_val >= self.settings.DRIFT_FEATURE_KS_WARN:
                ks_status = DriftStatus.WATCH
                ks_severity = DriftSeverity.MEDIUM

        metrics.append(DriftMetric(
            metric_name="ks_statistic",
            test_type=DriftTestType.KS_TEST,
            domain=DriftDomain.FEATURE,
            value=ks_val,
            threshold_warn=self.settings.DRIFT_FEATURE_KS_WARN,
            threshold_fail=self.settings.DRIFT_FEATURE_KS_FAIL,
            status=ks_status,
            severity=ks_severity,
            sample_count_reference=ref_count,
            sample_count_current=cur_count
        ))

        metrics.append(DriftMetric(
            metric_name="mean_shift",
            test_type=DriftTestType.MEAN_SHIFT,
            domain=DriftDomain.FEATURE,
            value=DriftStatistics.mean_shift(ref_vals, cur_vals),
            sample_count_reference=ref_count,
            sample_count_current=cur_count
        ))

        result.metrics = metrics
        status, severity = self.classify_feature_status(metrics)
        result.status = status
        result.severity = severity

        return result

    def detect_categorical_feature(self, feature_name: str, reference: pd.Series, current: pd.Series) -> FeatureDriftResult:
        ref_vals = reference.dropna()
        cur_vals = current.dropna()

        ref_count = len(ref_vals)
        cur_count = len(cur_vals)

        result = FeatureDriftResult(
            feature_name=feature_name,
            reference_summary={"unique": ref_vals.nunique(), "count": ref_count},
            current_summary={"unique": cur_vals.nunique(), "count": cur_count}
        )

        if ref_count < self.settings.DRIFT_MIN_SAMPLES or cur_count < self.settings.DRIFT_MIN_SAMPLES:
            result.status = DriftStatus.INSUFFICIENT_DATA
            result.severity = DriftSeverity.LOW
            result.warnings.append(f"Insufficient samples (Ref: {ref_count}, Cur: {cur_count})")
            return result

        all_cats = set(ref_vals.unique()).union(set(cur_vals.unique()))
        cat_to_num = {cat: i for i, cat in enumerate(all_cats)}

        ref_num = [cat_to_num[x] for x in ref_vals]
        cur_num = [cat_to_num[x] for x in cur_vals]

        psi_val = DriftStatistics.population_stability_index(ref_num, cur_num, bins=len(all_cats))

        psi_status = DriftStatus.STABLE
        psi_severity = DriftSeverity.LOW

        if psi_val is not None:
            if psi_val >= self.settings.DRIFT_FEATURE_PSI_SEVERE:
                psi_status = DriftStatus.SEVERE_DRIFT
                psi_severity = DriftSeverity.CRITICAL
            elif psi_val >= self.settings.DRIFT_FEATURE_PSI_FAIL:
                psi_status = DriftStatus.DRIFTING
                psi_severity = DriftSeverity.HIGH
            elif psi_val >= self.settings.DRIFT_FEATURE_PSI_WARN:
                psi_status = DriftStatus.WATCH
                psi_severity = DriftSeverity.MEDIUM

        result.metrics.append(DriftMetric(
            metric_name="categorical_psi",
            test_type=DriftTestType.CATEGORY_SHIFT,
            domain=DriftDomain.FEATURE,
            value=psi_val,
            threshold_warn=self.settings.DRIFT_FEATURE_PSI_WARN,
            threshold_fail=self.settings.DRIFT_FEATURE_PSI_FAIL,
            status=psi_status,
            severity=psi_severity,
            sample_count_reference=ref_count,
            sample_count_current=cur_count
        ))

        result.status = psi_status
        result.severity = psi_severity

        return result

    def feature_summary(self, series: pd.Series) -> dict[str, Any]:
        if not pd.api.types.is_numeric_dtype(series):
            return {"unique": series.nunique(), "count": len(series.dropna())}

        s = series.dropna()
        if len(s) == 0:
            return {"count": 0}

        return {
            "count": len(s),
            "mean": float(s.mean()),
            "std": float(s.std()) if len(s) > 1 else 0.0,
            "min": float(s.min()),
            "25%": float(s.quantile(0.25)),
            "50%": float(s.quantile(0.50)),
            "75%": float(s.quantile(0.75)),
            "max": float(s.max())
        }

    def classify_feature_status(self, metrics: list[DriftMetric]) -> tuple[DriftStatus, DriftSeverity]:
        severities = {
            DriftSeverity.CRITICAL: 4,
            DriftSeverity.HIGH: 3,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.LOW: 1,
            DriftSeverity.UNKNOWN: 0
        }

        max_severity = DriftSeverity.UNKNOWN
        worst_status = DriftStatus.STABLE

        for m in metrics:
            if m.status in [DriftStatus.SEVERE_DRIFT, DriftStatus.DRIFTING, DriftStatus.WATCH]:
                if severities[m.severity] > severities[max_severity]:
                    max_severity = m.severity
                    worst_status = m.status

        return worst_status, max_severity
