import os
from pathlib import Path

# Just overwrite the file for simplicity because we need these specific exceptions at the top.
ex_path = Path("bist_signal_bot/core/exceptions.py")
content = ex_path.read_text()

# We'll just define all the ones the tests failed on explicitly at the top
new_top = """
class BistSignalBotError(Exception): pass
class DataImportError(BistSignalBotError): pass
class DataImportAdapterError(DataImportError): pass
class SchemaMappingError(DataImportError): pass
class ImportPreviewError(DataImportError): pass
class ImportNormalizationError(DataImportError): pass
class ImportValidationError(DataImportError): pass
class LocalDataImporterError(DataImportError): pass
class ImportChunkingError(DataImportError): pass
class ImportProvenanceError(DataImportError): pass
class DataImportStorageError(DataImportError): pass
"""

ex_path.write_text(new_top + content)
