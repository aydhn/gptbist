import pytest
from datetime import datetime
from bist_signal_bot.knowledge.reporting import format_knowledge_report_markdown

def test_format_knowledge_report():
    stats = {
        "document_count": 10,
        "chunk_count": 20,
        "memory_card_count": 5,
        "last_build_status": "READY"
    }

    text = format_knowledge_report_markdown(stats)
    assert "Documents**: 10" in text
    assert "Chunks**: 20" in text
