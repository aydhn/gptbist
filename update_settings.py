import re

with open("bist_signal_bot/config/settings.py", "r") as f:
    content = f.read()

new_fields = """
    # Pattern Detection Features
    ENABLE_PATTERN_DETECTORS: bool = Field(default=True, description="Enable or disable pattern detectors.")
    PATTERN_FEATURE_LEVEL: str = Field(default="basic", description="Feature level for patterns: basic, advanced, or full.")
    PATTERN_BREAKOUT_WINDOW: int = Field(default=20, description="Window size for breakout detection.")
    PATTERN_SR_WINDOW: int = Field(default=50, description="Window size for support/resistance detection.")
    PATTERN_RANGE_WINDOW: int = Field(default=20, description="Window size for range structure detection.")
    PATTERN_VOLUME_WINDOW: int = Field(default=20, description="Window size for volume-confirmed breakouts.")
    PATTERN_VOLUME_MULTIPLIER: float = Field(default=1.5, description="Volume multiplier for confirmed breakouts.")
    PATTERN_GAP_THRESHOLD: float = Field(default=0.02, description="Percentage threshold for gap detection.")
    PATTERN_SR_TOLERANCE_PCT: float = Field(default=0.02, description="Tolerance percentage for support/resistance.")
    PATTERN_FALSE_BREAKOUT_LAG_BARS: int = Field(default=3, description="Lag bars for false breakout detection.")
    PATTERN_DOJI_BODY_THRESHOLD: float = Field(default=0.1, description="Body to range ratio threshold for Doji.")
"""

insertion_point = content.find("def model_post_init(self, __context: Any) -> None:")
content = content[:insertion_point] + new_fields + "\n    " + content[insertion_point:]

validation_rules = """
        if self.PATTERN_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_FEATURE_LEVEL must be basic, advanced, or full")

        if any(w <= 0 for w in [self.PATTERN_BREAKOUT_WINDOW, self.PATTERN_SR_WINDOW,
                               self.PATTERN_RANGE_WINDOW, self.PATTERN_VOLUME_WINDOW,
                               self.PATTERN_FALSE_BREAKOUT_LAG_BARS]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern window/lag parameters must be positive")

        if self.PATTERN_VOLUME_MULTIPLIER <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_VOLUME_MULTIPLIER must be positive")

        if self.PATTERN_GAP_THRESHOLD < 0 or self.PATTERN_SR_TOLERANCE_PCT < 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern thresholds and tolerances cannot be negative")

        if not (0 <= self.PATTERN_DOJI_BODY_THRESHOLD <= 1):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_DOJI_BODY_THRESHOLD must be between 0 and 1")
"""

validation_insertion_point = content.find("profile = get_profile(self.APP_ENV)")
content = content[:validation_insertion_point] + validation_rules + "\n        " + content[validation_insertion_point:]

with open("bist_signal_bot/config/settings.py", "w") as f:
    f.write(content)
