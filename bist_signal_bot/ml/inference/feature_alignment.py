import pandas as pd
from typing import Any

from bist_signal_bot.ml.inference.models import MLFeatureAlignmentResult, MLFeatureAlignmentStatus
from bist_signal_bot.core.exceptions import MLFeatureAlignmentError

class MLFeatureAligner:

    def align_features(self, data: pd.DataFrame, required_features: list[str], allow_extra_features: bool = True, reject_on_missing: bool = True) -> MLFeatureAlignmentResult:
        df = data.copy()

        self.validate_required_features(required_features)

        available = list(df.columns)
        missing = [f for f in required_features if f not in available]
        extra = [f for f in available if f not in required_features]
        issues = []
        status = MLFeatureAlignmentStatus.ALIGNED

        if missing:
            if reject_on_missing:
                status = MLFeatureAlignmentStatus.MISSING_FEATURES
                issues.append(f"Missing required features: {missing}")
                return MLFeatureAlignmentResult(
                    status=status,
                    required_features=required_features,
                    available_features=available,
                    missing_features=missing,
                    extra_features=extra,
                    aligned_data=None,
                    issues=issues
                )
            else:
                for col in missing:
                    df[col] = float('nan')
                issues.append(f"Warning: Inserted NaN for missing features: {missing}")
                status = MLFeatureAlignmentStatus.ALIGNED # Proceed with NaNs

        if extra:
            if not allow_extra_features:
                status = MLFeatureAlignmentStatus.EXTRA_FEATURES
                issues.append(f"Extra features found but allow_extra_features is False: {extra}")
                return MLFeatureAlignmentResult(
                    status=status,
                    required_features=required_features,
                    available_features=available,
                    missing_features=missing,
                    extra_features=extra,
                    aligned_data=None,
                    issues=issues
                )

        # Only select required, and exactly in order
        aligned_data = df[required_features]

        return MLFeatureAlignmentResult(
            status=status,
            required_features=required_features,
            available_features=available,
            missing_features=missing,
            extra_features=extra,
            aligned_data=aligned_data,
            issues=issues
        )

    def validate_required_features(self, required_features: list[str]) -> None:
        forbidden = ["label", "target", "future", "fwd", "forward", "next", "lead", "shifted_minus"]
        for feat in required_features:
            feat_lower = feat.lower()
            if any(f in feat_lower for f in forbidden):
                raise MLFeatureAlignmentError(f"CRITICAL: required feature {feat} contains a forbidden keyword hinting at future data leakage.")

    def compare_live_schema_to_artifact(self, data_cols: list[str], artifact_feature_cols: list[str]) -> dict[str, Any]:
        missing = [f for f in artifact_feature_cols if f not in data_cols]
        extra = [f for f in data_cols if f not in artifact_feature_cols]
        return {
            "is_match": len(missing) == 0,
            "missing": missing,
            "extra": extra
        }

    def feature_alignment_report_text(self, result: MLFeatureAlignmentResult) -> str:
        report = [f"Alignment Status: {result.status.value}"]
        if result.missing_features:
            report.append(f"Missing Features: {result.missing_features}")
        if result.extra_features:
            report.append(f"Extra Features (Ignored/Rejected): {result.extra_features}")
        if result.issues:
            report.append("Issues:")
            for issue in result.issues:
                report.append(f"  - {issue}")
        return "\n".join(report)
