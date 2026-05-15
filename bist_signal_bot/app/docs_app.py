from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.docs.generator import DocsGenerator
from bist_signal_bot.docs.validator import DocsValidator
from bist_signal_bot.docs.catalog import CommandCatalogBuilder
from bist_signal_bot.docs.storage import DocsStore

def create_docs_generator(settings: Settings | None = None) -> DocsGenerator:
    return DocsGenerator(catalog_builder=CommandCatalogBuilder(), settings=settings)

def create_docs_validator(settings: Settings | None = None) -> DocsValidator:
    return DocsValidator(settings=settings)

def create_command_catalog_builder(settings: Settings | None = None) -> CommandCatalogBuilder:
    return CommandCatalogBuilder()

def create_docs_store(settings: Settings | None = None, base_dir: Path | None = None) -> DocsStore:
    return DocsStore(base_dir)
