from typing import Any
import pandas as pd
import time
from datetime import datetime, UTC
from bist_signal_bot.patterns.base import BasePatternDetector
from bist_signal_bot.patterns.models import (
    PatternCategory, PatternRequest, PatternResult, PatternBatchResult,
    PatternStatus, PatternIssue, PatternSpec
)
from bist_signal_bot.core.exceptions import PatternEngineError, PatternValidationError

class PatternRegistry:
    def __init__(self):
        self._detectors: dict[str, BasePatternDetector] = {}

    def register(self, detector: BasePatternDetector) -> None:
        name = detector.spec.name
        if name in self._detectors:
            raise ValueError(f"Detector {name} is already registered")
        self._detectors[name] = detector

    def get(self, name: str) -> BasePatternDetector:
        if name not in self._detectors:
            raise PatternEngineError(f"Detector not found: {name}")
        return self._detectors[name]

    def exists(self, name: str) -> bool:
        return name in self._detectors

    def list_specs(self, category: PatternCategory | None = None) -> list[PatternSpec]:
        specs = [d.spec for d in self._detectors.values()]
        if category:
            specs = [s for s in specs if s.category == category]
        return specs

    def list_names(self, category: PatternCategory | None = None) -> list[str]:
        return [s.name for s in self.list_specs(category)]

    @classmethod
    def create_default_pattern_registry(cls) -> "PatternRegistry":
        registry = cls()

        # Candles
        from bist_signal_bot.patterns.candles import (
            CandleBodyMetricsDetector, DojiDetector, HammerDetector,
            EngulfingDetector, InsideOutsideBarDetector, MarubozuDetector, CandleCompositeDetector
        )
        registry.register(CandleBodyMetricsDetector())
        registry.register(DojiDetector())
        registry.register(HammerDetector())
        registry.register(EngulfingDetector())
        registry.register(InsideOutsideBarDetector())
        registry.register(MarubozuDetector())
        registry.register(CandleCompositeDetector())

        # Price Action
        from bist_signal_bot.patterns.price_action import (
            RollingHighLowDetector, SwingPointDetector, MarketStructureStateDetector,
            RangePositionDetector, RangeCompressionDetector
        )
        registry.register(RollingHighLowDetector())
        registry.register(SwingPointDetector())
        registry.register(MarketStructureStateDetector())
        registry.register(RangePositionDetector())
        registry.register(RangeCompressionDetector())

        # Breakouts
        from bist_signal_bot.patterns.breakouts import (
            PriceBreakoutDetector, VolumeConfirmedBreakoutDetector, LaggedFalseBreakoutDetector,
            BreakoutRetestDetector, GapBreakoutDetector, BreakoutCompositeDetector
        )
        registry.register(PriceBreakoutDetector())
        registry.register(VolumeConfirmedBreakoutDetector())
        registry.register(LaggedFalseBreakoutDetector())
        registry.register(BreakoutRetestDetector())
        registry.register(GapBreakoutDetector())
        registry.register(BreakoutCompositeDetector())

        # Support/Resistance
        from bist_signal_bot.patterns.support_resistance import (
            RollingSupportResistanceDetector, PivotPointsDetector, SRTouchCountDetector,
            NearSRDetector, SRCompositeDetector
        )
        registry.register(RollingSupportResistanceDetector())
        registry.register(PivotPointsDetector())
        registry.register(SRTouchCountDetector())
        registry.register(NearSRDetector())
        registry.register(SRCompositeDetector())

        return registry

class PatternEngine:
    def __init__(self, registry: PatternRegistry | None = None, settings: Any = None):
        self.registry = registry or PatternRegistry.create_default_pattern_registry()
        self.settings = settings

    def detect(self, data: Any, request: PatternRequest) -> tuple[pd.DataFrame, PatternResult]:
        df = data.data if hasattr(data, 'data') else data

        start_time = time.time()
        issues = []

        try:
            detector = self.registry.get(request.name)
            merged_params = {**detector.spec.default_params, **request.params}
            output_cols = detector.get_output_columns(merged_params)

            result_df = detector(df, **merged_params)

            # Use original index
            result_df.index = df.index

            # Apply prefix if requested
            if request.output_prefix:
                result_df = result_df.add_prefix(request.output_prefix)
                output_cols = [f"{request.output_prefix}{c}" for c in output_cols]

            # Count actual detections (sum of abs values across boolean-like columns > 0 on last row logic or overall)
            # For this simple implementation, we just sum non-null values.
            detected_count = result_df.notna().sum().sum()

            res = PatternResult(
                pattern=request.name,
                status=PatternStatus.SUCCESS,
                output_columns=output_cols,
                row_count=len(df),
                detected_count=int(detected_count),
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )
            return result_df, res

        except Exception as e:
            issues.append(PatternIssue(pattern=request.name, message=str(e), severity="ERROR"))
            res = PatternResult(
                pattern=request.name,
                status=PatternStatus.FAILED,
                output_columns=[],
                row_count=len(df),
                detected_count=0,
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )
            return pd.DataFrame(index=df.index), res

    def detect_many(self, data: Any, requests: list[PatternRequest], continue_on_error: bool = True) -> PatternBatchResult:
        df = data.data if hasattr(data, 'data') else data
        start_time = time.time()

        results = []
        output_dfs = []
        success_count = 0
        failed_count = 0

        for req in requests:
            res_df, res = self.detect(df, req)
            results.append(res)

            if res.status == PatternStatus.SUCCESS:
                output_dfs.append(res_df)
                success_count += 1
            else:
                failed_count += 1
                if not continue_on_error:
                    raise PatternEngineError(f"Pattern detection failed for {req.name}: {res.issues[0].message}")

        final_df = pd.concat([df] + output_dfs, axis=1) if output_dfs else df.copy()

        return PatternBatchResult(
            results=results,
            output_data=final_df,
            requested_count=len(requests),
            success_count=success_count,
            failed_count=failed_count,
            elapsed_seconds=time.time() - start_time,
            generated_at=datetime.now(UTC)
        )

    def parse_requests(self, raw: list[str]) -> list[PatternRequest]:
        requests = []
        for r in raw:
            parts = r.split(":", 1)
            name = parts[0]
            params = {}
            if len(parts) > 1:
                param_pairs = parts[1].split(",")
                for p in param_pairs:
                    k, v = p.split("=")
                    try:
                        v = float(v) if "." in v else int(v)
                    except ValueError:
                        pass
                    params[k] = v
            requests.append(PatternRequest(name=name, params=params))
        return requests

    def detect_default_set(self, data: Any) -> PatternBatchResult:
        from bist_signal_bot.features.pattern_features import PatternFeatureBuilder
        builder = PatternFeatureBuilder(self, self.settings)
        return builder.build_basic_pattern_features(data)
