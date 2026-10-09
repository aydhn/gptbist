import io
import sys

from bist_signal_bot.cli.main import _ensure_utf8_stdio


def test_ensure_utf8_stdio_reconfigures_streams(monkeypatch):
    raw_out = io.BytesIO()
    raw_err = io.BytesIO()
    out = io.TextIOWrapper(raw_out, encoding="cp1252", errors="strict")
    err = io.TextIOWrapper(raw_err, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    _ensure_utf8_stdio()

    assert out.encoding.lower().replace("_", "-") == "utf-8"
    assert err.encoding.lower().replace("_", "-") == "utf-8"
    print("İş Bankası ğüşıöç \u2713", file=out)  # would raise under cp1252 strict
    out.flush()
    assert "İş".encode("utf-8") in raw_out.getvalue()


def test_ensure_utf8_stdio_tolerates_streams_without_reconfigure(monkeypatch):
    class Dummy:
        def write(self, s):
            return len(s)

    monkeypatch.setattr(sys, "stdout", Dummy())
    monkeypatch.setattr(sys, "stderr", Dummy())
    _ensure_utf8_stdio()
