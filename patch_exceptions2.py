import os
from pathlib import Path

ex_path = Path("bist_signal_bot/core/exceptions.py")
content = ex_path.read_text()

# Looks like it has BistSignalBotError defined somewhere but it's not clear.
# To be safe we will just inject our classes at the very top of the file right after imports or at the end.
if "class DataImportError(" not in content:
    content += """

class DataImportError(Exception):
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
