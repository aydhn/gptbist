from typing import Any
from bist_signal_bot.patterns.engine import PatternEngine, PatternRegistry
from bist_signal_bot.patterns.models import PatternRequest, PatternBatchResult

class PatternFeatureBuilder:
    def __init__(self, pattern_engine: PatternEngine | None = None, settings: Any = None):
        self.settings = settings
        self.engine = pattern_engine or PatternEngine(settings=settings)

    def default_pattern_requests(self, level: str = "basic") -> list[PatternRequest]:
        w_breakout = self.settings.PATTERN_BREAKOUT_WINDOW if self.settings else 20
        w_sr = self.settings.PATTERN_SR_WINDOW if self.settings else 50
        w_range = self.settings.PATTERN_RANGE_WINDOW if self.settings else 20
        w_vol = self.settings.PATTERN_VOLUME_WINDOW if self.settings else 20
        v_mult = self.settings.PATTERN_VOLUME_MULTIPLIER if self.settings else 1.5
        lag = self.settings.PATTERN_FALSE_BREAKOUT_LAG_BARS if self.settings else 3
        gap = self.settings.PATTERN_GAP_THRESHOLD if self.settings else 0.02
        tol = self.settings.PATTERN_SR_TOLERANCE_PCT if self.settings else 0.02
        doji = self.settings.PATTERN_DOJI_BODY_THRESHOLD if self.settings else 0.1

        basic = [
            PatternRequest("candle_body_metrics"),
            PatternRequest("doji", {"body_threshold": doji}),
            PatternRequest("inside_outside_bar"),
            PatternRequest("price_breakout", {"window": w_breakout}),
            PatternRequest("rolling_sr", {"window": w_sr}),
            PatternRequest("range_position", {"window": w_range})
        ]

        advanced = [
            PatternRequest("engulfing"),
            PatternRequest("hammer"),
            PatternRequest("market_structure_state", {"window": w_range}),
            PatternRequest("volume_confirmed_breakout", {
                "price_window": w_breakout, "volume_window": w_vol, "volume_multiplier": v_mult
            }),
            PatternRequest("false_breakout", {"window": w_breakout, "fail_within_bars": lag}),
            PatternRequest("breakout_retest", {"window": w_breakout, "tolerance_pct": tol}),
            PatternRequest("pivot_points"),
            PatternRequest("sr_touch_count", {"window": w_sr, "tolerance_pct": tol}),
            PatternRequest("breakout_composite", {"price_window": w_breakout, "volume_window": w_vol}),
            PatternRequest("sr_composite", {"window": w_sr})
        ]

        if level == "basic":
            return basic
        elif level == "advanced":
            return advanced
        elif level == "full":
            return basic + advanced
        else:
            raise ValueError(f"Unknown pattern feature level: {level}")

    def build_basic_pattern_features(self, market_data: Any) -> PatternBatchResult:
        requests = self.default_pattern_requests("basic")
        return self.engine.detect_many(market_data, requests)

    def build_advanced_pattern_features(self, market_data: Any) -> PatternBatchResult:
        requests = self.default_pattern_requests("advanced")
        return self.engine.detect_many(market_data, requests)

    def build_full_pattern_features(self, market_data: Any) -> PatternBatchResult:
        requests = self.default_pattern_requests("full")
        return self.engine.detect_many(market_data, requests)

    def add_features(self, market_data, level: str = "basic"):
        return market_data.copy()
