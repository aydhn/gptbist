import pytest
from bist_signal_bot.disclosures.normalizer import DisclosureNormalizer
from bist_signal_bot.disclosures.models import DisclosureRecord
from datetime import datetime

def test_disclosure_normalizer_text():
    normalizer = DisclosureNormalizer()
    text = "  Bu bir   test  \n\n metnidir.  "
    normalized = normalizer.normalize_text(text)
    assert normalized == "Bu bir test metnidir."

def test_disclosure_normalizer_redact():
    normalizer = DisclosureNormalizer()
    text = "My secret token is 12345-ABCDE-67890."
    redacted = normalizer.redact_sensitive_text(text)
    assert "12345" not in redacted
    assert "[REDACTED]" in redacted
