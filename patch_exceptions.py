import os
from pathlib import Path

# Create base exceptions if they don't exist
ex_path = Path("bist_signal_bot/core/exceptions.py")
if not ex_path.exists():
    ex_path.parent.mkdir(parents=True, exist_ok=True)
    ex_path.write_text("class BistSignalBotError(Exception):\n    pass\n")

content = ex_path.read_text()
if "DataImportError" not in content:
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
