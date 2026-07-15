from typing import Optional
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.docs_hub.storage import DocsHubStore
from bist_signal_bot.docs_hub.indexer import DocsIndexer
from bist_signal_bot.docs_hub.search import DocsSearchEngine
from bist_signal_bot.docs_hub.architecture import ArchitectureMapBuilder
from bist_signal_bot.docs_hub.cookbook import CommandCookbookBuilder
from bist_signal_bot.docs_hub.troubleshooting import TroubleshootingKBBuilder
from bist_signal_bot.docs_hub.coverage import DocsCoverageAnalyzer
from bist_signal_bot.docs_hub.handoff import MVPHandoffBuilder

def create_docs_hub_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DocsHubStore:
    return DocsHubStore(settings, base_dir)

def create_docs_indexer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DocsIndexer:
    return DocsIndexer(settings, base_dir)

def create_docs_search_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DocsSearchEngine:
    return DocsSearchEngine(settings, base_dir)

def create_architecture_map_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ArchitectureMapBuilder:
    return ArchitectureMapBuilder()

def create_command_cookbook_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> CommandCookbookBuilder:
    return CommandCookbookBuilder(settings, base_dir)

def create_troubleshooting_kb_builder(settings: Optional[Settings] = None) -> TroubleshootingKBBuilder:
    return TroubleshootingKBBuilder(settings)

def create_docs_coverage_analyzer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DocsCoverageAnalyzer:
    return DocsCoverageAnalyzer(settings, base_dir)

def create_mvp_handoff_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MVPHandoffBuilder:
    return MVPHandoffBuilder(settings, base_dir)
