import pytest
from bist_signal_bot.patterns.models import PatternSpec, PatternCategory

def test_pattern_spec_validation():
    spec = PatternSpec(
        name="test_pattern",
        display_name="Test Pattern",
        category=PatternCategory.BREAKOUT,
        required_columns=["high", "low"],
        default_params={"window": 20},
        output_columns=["out_1"],
        min_rows=10
    )
    assert spec.name == "test_pattern"
    assert spec.category == PatternCategory.BREAKOUT
    assert spec.min_rows == 10
