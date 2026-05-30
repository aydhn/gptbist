from datetime import datetime, timezone
from bist_signal_bot.feature_store.models import FeatureFrame, FeatureSet

class FeatureServingEngine:
    def serve_for_scanner(self, symbols: list[str], as_of: datetime | None = None) -> FeatureFrame:
        now = as_of or datetime.now(timezone.utc)
        return FeatureFrame(
            frame_id=f"frame_scanner_{now.timestamp()}",
            feature_set_id="fs_scanner_core_v1",
            symbols=symbols,
            as_of=now,
            row_count=0,
            column_count=0,
            point_in_time_safe=True
        )

    def serve_for_ml(self, symbols: list[str], feature_set_name: str = "ml_core_v1", as_of: datetime | None = None) -> FeatureFrame:
        now = as_of or datetime.now(timezone.utc)
        return FeatureFrame(
            frame_id=f"frame_ml_{now.timestamp()}",
            feature_set_id=feature_set_name,
            symbols=symbols,
            as_of=now,
            row_count=0,
            column_count=0,
            point_in_time_safe=True
        )

    def serve_for_backtest(self, symbols: list[str], as_of: datetime, feature_set_name: str = "validation_core_v1") -> FeatureFrame:
        return FeatureFrame(
            frame_id=f"frame_backtest_{as_of.timestamp()}",
            feature_set_id=feature_set_name,
            symbols=symbols,
            as_of=as_of,
            row_count=0,
            column_count=0,
            point_in_time_safe=True
        )

    def serve_for_context(self, symbol: str, as_of: datetime | None = None) -> FeatureFrame:
        now = as_of or datetime.now(timezone.utc)
        return FeatureFrame(
            frame_id=f"frame_context_{now.timestamp()}",
            feature_set_id="fs_context_light_v1",
            symbols=[symbol],
            as_of=now,
            row_count=0,
            column_count=0,
            point_in_time_safe=True
        )

    def validate_served_frame(self, frame: FeatureFrame, feature_set: FeatureSet) -> list[str]:
        errors = []
        if frame.feature_set_id != feature_set.feature_set_id and frame.feature_set_id != feature_set.name:
            errors.append("Feature set mismatch")
        return errors
