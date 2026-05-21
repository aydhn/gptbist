import pytest
from bist_signal_bot.review.thesis import ReviewThesisBuilder
from bist_signal_bot.review.models import ThesisStrength

def test_thesis_create():
    builder = ReviewThesisBuilder()
    t = builder.create_thesis("1", "ASELS", "Good trend, moving averages are aligning nicely.", "Wait for pullback", ["Risk1", "Risk2", "Risk3", "Risk4"])
    assert t.symbol == "ASELS"
    assert t.main_thesis == "Good trend, moving averages are aligning nicely."
    assert len(t.key_risks) == 4

    strength = builder.score_thesis_strength(t, [])
    assert strength == ThesisStrength.MODERATE

def test_thesis_sanitize():
    builder = ReviewThesisBuilder()
    t = builder.create_thesis("1", "THYAO", "Bu fırsat kaçmaz, kesin al 100% garanti", "")
    assert "REDACTED" in t.main_thesis
