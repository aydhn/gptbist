with open("bist_signal_bot/config/settings.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == "class Settings(BaseSettings):":
        lines.insert(i+1, "    # Pattern Detection Features\n")
        lines.insert(i+2, "    ENABLE_PATTERN_DETECTORS: bool = Field(default=True, description=\"Enable or disable pattern detectors.\")\n")
        lines.insert(i+3, "    PATTERN_FEATURE_LEVEL: str = Field(default=\"basic\", description=\"Feature level for patterns: basic, advanced, or full.\")\n")
        lines.insert(i+4, "    PATTERN_BREAKOUT_WINDOW: int = Field(default=20, description=\"Window size for breakout detection.\")\n")
        lines.insert(i+5, "    PATTERN_SR_WINDOW: int = Field(default=50, description=\"Window size for support/resistance detection.\")\n")
        lines.insert(i+6, "    PATTERN_RANGE_WINDOW: int = Field(default=20, description=\"Window size for range structure detection.\")\n")
        lines.insert(i+7, "    PATTERN_VOLUME_WINDOW: int = Field(default=20, description=\"Window size for volume-confirmed breakouts.\")\n")
        lines.insert(i+8, "    PATTERN_VOLUME_MULTIPLIER: float = Field(default=1.5, description=\"Volume multiplier for confirmed breakouts.\")\n")
        lines.insert(i+9, "    PATTERN_GAP_THRESHOLD: float = Field(default=0.02, description=\"Percentage threshold for gap detection.\")\n")
        lines.insert(i+10, "    PATTERN_SR_TOLERANCE_PCT: float = Field(default=0.02, description=\"Tolerance percentage for support/resistance.\")\n")
        lines.insert(i+11, "    PATTERN_FALSE_BREAKOUT_LAG_BARS: int = Field(default=3, description=\"Lag bars for false breakout detection.\")\n")
        lines.insert(i+12, "    PATTERN_DOJI_BODY_THRESHOLD: float = Field(default=0.1, description=\"Body to range ratio threshold for Doji.\")\n\n")
        break

# Clean up the rogue declarations that were put in the wrong place earlier
cleaned_lines = []
for line in lines:
    if line.strip().startswith("ENABLE_PATTERN") and "def model_post_init" in "".join(lines):
        pass # ignore
    elif line.strip().startswith("PATTERN_"):
        pass # ignore
    else:
        cleaned_lines.append(line)

with open("bist_signal_bot/config/settings.py", "w") as f:
    f.writelines(lines)
