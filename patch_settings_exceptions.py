import os
from pathlib import Path

# Fix exceptions.py
ex_path = Path("bist_signal_bot/core/exceptions.py")
if ex_path.exists():
    content = ex_path.read_text()
    if "class DataImportError(BistSignalBotError):" not in content:
        content += """

class DataImportError(BistSignalBotError):
    pass

class DataImportAdapterError(DataImportError):
    pass

class SchemaMappingError(DataImportError):
    pass

class ImportPreviewError(DataImportError):
    pass

class ImportNormalizationError(DataImportError):
    pass

class ImportValidationError(DataImportError):
    pass

class LocalDataImporterError(DataImportError):
    pass

class ImportChunkingError(DataImportError):
    pass

class ImportProvenanceError(DataImportError):
    pass

class DataImportStorageError(DataImportError):
    pass
"""
        ex_path.write_text(content)

# Fix settings indentation
settings_path = Path("bist_signal_bot/config/settings.py")
if settings_path.exists():
    content = settings_path.read_text()
    import re
    # Remove the bad block
    content = re.sub(r"    # Data Import Settings\n    ENABLE_DATA_IMPORT: bool = True.*?RESEARCH_AUTO_LOG_DATA_IMPORT: bool = False\n", "", content, flags=re.DOTALL)

    # Re-insert with 4 spaces exactly before the final block or somewhere safe
    # Let's find a class definition or just append if it's missing

    if "class Settings" in content:
         # Find the last line of Settings or just before a new class
         new_block = """
    # Data Import Settings
    ENABLE_DATA_IMPORT: bool = True
    DATA_IMPORT_DIR_NAME: str = "data_import"
    DATA_IMPORT_RESEARCH_ONLY: bool = True
    DATA_IMPORT_SAVE_RESULTS: bool = True

    DATA_IMPORT_ENABLE_CSV: bool = True
    DATA_IMPORT_ENABLE_JSON: bool = True
    DATA_IMPORT_ENABLE_JSONL: bool = True
    DATA_IMPORT_ENABLE_PARQUET: bool = True
    DATA_IMPORT_ENABLE_SQLITE: bool = True
    DATA_IMPORT_ENABLE_EXCEL: bool = False

    DATA_IMPORT_PREVIEW_MAX_ROWS: int = 20
    DATA_IMPORT_INFER_TYPES: bool = True
    DATA_IMPORT_ROW_COUNT_ESTIMATE: bool = True

    DATA_IMPORT_AUTO_SCHEMA_MAPPING: bool = True
    DATA_IMPORT_MAPPING_MIN_CONFIDENCE: float = 60.0
    DATA_IMPORT_FAIL_ON_MISSING_REQUIRED: bool = True

    DATA_IMPORT_NORMALIZE_SYMBOLS: bool = True
    DATA_IMPORT_NORMALIZE_DATES: bool = True
    DATA_IMPORT_NORMALIZE_DECIMAL_COMMA: bool = True
    DATA_IMPORT_DROP_INVALID_REQUIRED_ROWS: bool = True
    DATA_IMPORT_DEDUPLICATE: bool = True

    DATA_IMPORT_CHUNKING_ENABLED: bool = True
    DATA_IMPORT_CHUNK_SIZE: int = 50000
    DATA_IMPORT_MAX_ROWS_MEMORY: int = 250000

    DATA_IMPORT_DEFAULT_DRY_RUN: bool = True
    DATA_IMPORT_WRITE_REQUIRES_CONFIRM: bool = True
    DATA_IMPORT_REGISTER_CATALOG_REQUIRES_CONFIRM: bool = True

    RUNTIME_DATA_IMPORT_ENABLED: bool = True
    QA_INCLUDE_DATA_IMPORT: bool = True
    OPS_INCLUDE_DATA_IMPORT: bool = True
    REPORT_INCLUDE_DATA_IMPORT: bool = True
    RESEARCH_AUTO_LOG_DATA_IMPORT: bool = False
"""
         content = content.replace("class Settings(BaseSettings):", "class Settings(BaseSettings):\n" + new_block)
         settings_path.write_text(content)
