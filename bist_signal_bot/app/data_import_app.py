from pathlib import Path
from typing import Any

from bist_signal_bot.data_import.storage import DataImportStore
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine
from bist_signal_bot.data_import.preview import ImportPreviewBuilder
from bist_signal_bot.data_import.normalization import ImportNormalizer
from bist_signal_bot.data_import.validation import ImportValidationEngine
from bist_signal_bot.data_import.importer import LocalDataImporter
from bist_signal_bot.data_import.chunking import ImportChunkReader
from bist_signal_bot.data_import.provenance import ImportProvenanceBuilder

def create_data_import_store(settings: Any = None, base_dir: Path | None = None) -> DataImportStore:
    return DataImportStore(settings, base_dir)

def create_local_import_adapter_registry(settings: Any = None, base_dir: Path | None = None) -> LocalImportAdapterRegistry:
    return LocalImportAdapterRegistry(settings, base_dir)

def create_schema_mapping_engine(settings: Any = None) -> SchemaMappingEngine:
    return SchemaMappingEngine(settings)

def create_import_preview_builder(settings: Any = None, base_dir: Path | None = None) -> ImportPreviewBuilder:
    return ImportPreviewBuilder(settings, base_dir)

def create_import_normalizer(settings: Any = None) -> ImportNormalizer:
    return ImportNormalizer(settings)

def create_import_validation_engine(settings: Any = None, base_dir: Path | None = None) -> ImportValidationEngine:
    return ImportValidationEngine(settings, base_dir)

def create_local_data_importer(settings: Any = None, base_dir: Path | None = None) -> LocalDataImporter:
    return LocalDataImporter(settings, base_dir)

def create_import_chunk_reader(settings: Any = None, base_dir: Path | None = None) -> ImportChunkReader:
    return ImportChunkReader(settings, base_dir)

def create_import_provenance_builder(settings: Any = None, base_dir: Path | None = None) -> ImportProvenanceBuilder:
    return ImportProvenanceBuilder(settings, base_dir)
