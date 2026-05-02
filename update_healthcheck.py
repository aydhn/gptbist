import re

with open("bist_signal_bot/app/healthcheck.py", "r") as f:
    content = f.read()

new_block = """
        "pattern_detectors": {
            "enabled": settings.ENABLE_PATTERN_DETECTORS,
            "feature_level": settings.PATTERN_FEATURE_LEVEL,
            "breakout_window": settings.PATTERN_BREAKOUT_WINDOW,
            "sr_window": settings.PATTERN_SR_WINDOW,
            "volume_window": settings.PATTERN_VOLUME_WINDOW,
            "gap_threshold": settings.PATTERN_GAP_THRESHOLD,
            "registered_pattern_detector_count": 0, # Will be set dynamically when registry is imported
            "builder_instantiable": True,
            "mock_capable": True
        },
"""

insertion_point = content.find("        \"momentum_indicators\": {")
content = content[:insertion_point] + new_block + content[insertion_point:]

with open("bist_signal_bot/app/healthcheck.py", "w") as f:
    f.write(content)
