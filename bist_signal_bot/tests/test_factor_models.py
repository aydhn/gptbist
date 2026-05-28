
from bist_signal_bot.factors.models import FactorInputSnapshot, FactorScore, FactorType, FactorStatus, FactorExposure, ThemeDefinition
import pytest
from datetime import datetime

def test_factor_input_validation():
    snap = FactorInputSnapshot(input_id="1", symbol="asels", as_of=datetime.now(), valuation_score=150.0, price_return_20d_pct=None)
    assert snap.symbol == "ASELS"
    assert snap.valuation_score == 100.0
    assert "Missing core price momentum input" in snap.warnings

def test_factor_score_clamp():
    s = FactorScore(score_id="1", symbol="THYAO", factor_type=FactorType.MOMENTUM, as_of=datetime.now(), score=120)
    assert s.score == 100.0
    assert "research-only" in s.disclaimer

def test_theme_definition():
    t = ThemeDefinition(theme_id="t1", name="Defense", description="D")
    assert "research metadata" in t.disclaimer
