import pytest
from bist_signal_bot.security.claims_guard import UnsafeClaimGuard
from bist_signal_bot.core.exceptions import UnsafeClaimError

def test_unsafe_claim_guard_catches_claims():
    with pytest.raises(UnsafeClaimError):
        UnsafeClaimGuard.validate_text("Bu sinyal kesin al diyor.")

    with pytest.raises(UnsafeClaimError):
        UnsafeClaimGuard.validate_text("Garanti kazanç fırsatı.")

    # Safe text should pass
    UnsafeClaimGuard.validate_text("Sinyal güçlü görünüyor, araştırma amaçlıdır.")

def test_unsafe_claim_guard_sanitizes_text():
    text = "Sinyal üretildi, kesin al fırsatı."
    sanitized = UnsafeClaimGuard.sanitize_text(text)

    assert "kesin al" not in sanitized.lower()
    assert "araştırma amaçlı alım adayı" in sanitized.lower()

def test_unsafe_claim_guard_sanitizes_payload():
    payload = {
        "msg": "gerçek işlem açıldı",
        "nested": ["yatırım tavsiyesidir"]
    }
    sanitized = UnsafeClaimGuard.sanitize_payload(payload)
    assert "gerçek işlem açıldı" not in sanitized["msg"].lower()
    assert "yatırım tavsiyesidir" not in sanitized["nested"][0].lower()
