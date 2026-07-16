import pytest
from pathlib import Path
from bist_signal_bot.docs.generator import DocsGenerator

def test_generate_configuration():
    gen = DocsGenerator()
    content = gen.generate_configuration()
    assert "TELEGRAM_BOT_TOKEN=" in content
    assert "your_telegram_bot_token_here" in content
    assert "<your_telegram_bot_token_here>" in content
