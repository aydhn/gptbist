import pytest
from bist_signal_bot.knowledge.sources import KnowledgeSourceCollector

def test_knowledge_source_collector(tmp_path):
    collector = KnowledgeSourceCollector()
    collector.data_dir = tmp_path

    docs = collector.collect_from_research_ledger()
    assert len(docs) == 0
