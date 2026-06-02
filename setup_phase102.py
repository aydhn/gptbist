import os
from pathlib import Path

# update core/exceptions.py
ex_path = Path("bist_signal_bot/core/exceptions.py")
if ex_path.exists():
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

# update storage/paths.py
paths_path = Path("bist_signal_bot/storage/paths.py")
if paths_path.exists():
    content = paths_path.read_text()
    if "get_data_import_dir" not in content:
        content += """
def get_data_import_dir(settings=None) -> Path:
    base = get_data_dir(settings)
    d = base / (settings.DATA_IMPORT_DIR_NAME if settings and hasattr(settings, "DATA_IMPORT_DIR_NAME") else "data_import")
    d.mkdir(parents=True, exist_ok=True)
    return d
"""
        paths_path.write_text(content)

# update core/audit.py
audit_path = Path("bist_signal_bot/core/audit.py")
if audit_path.exists():
    content = audit_path.read_text()
    if "DATA_IMPORT_SOURCE_BUILT" not in content:
        if "    # Phase" in content:
            content = content.replace("    # Phase", "    DATA_IMPORT_SOURCE_BUILT = 'DATA_IMPORT_SOURCE_BUILT'\n    DATA_IMPORT_PREVIEW_CREATED = 'DATA_IMPORT_PREVIEW_CREATED'\n    DATA_IMPORT_SCHEMA_MAPPING_CREATED = 'DATA_IMPORT_SCHEMA_MAPPING_CREATED'\n    DATA_IMPORT_VALIDATED = 'DATA_IMPORT_VALIDATED'\n    DATA_IMPORT_NORMALIZED = 'DATA_IMPORT_NORMALIZED'\n    DATA_IMPORT_JOB_RUN = 'DATA_IMPORT_JOB_RUN'\n    DATA_IMPORT_CATALOG_REGISTERED = 'DATA_IMPORT_CATALOG_REGISTERED'\n    DATA_IMPORT_REPORT_CREATED = 'DATA_IMPORT_REPORT_CREATED'\n    # Phase", 1)
        elif "class AuditEventType(str, Enum):" in content:
             content = content.replace("class AuditEventType(str, Enum):", "class AuditEventType(str, Enum):\n    DATA_IMPORT_SOURCE_BUILT = 'DATA_IMPORT_SOURCE_BUILT'\n    DATA_IMPORT_PREVIEW_CREATED = 'DATA_IMPORT_PREVIEW_CREATED'\n    DATA_IMPORT_SCHEMA_MAPPING_CREATED = 'DATA_IMPORT_SCHEMA_MAPPING_CREATED'\n    DATA_IMPORT_VALIDATED = 'DATA_IMPORT_VALIDATED'\n    DATA_IMPORT_NORMALIZED = 'DATA_IMPORT_NORMALIZED'\n    DATA_IMPORT_JOB_RUN = 'DATA_IMPORT_JOB_RUN'\n    DATA_IMPORT_CATALOG_REGISTERED = 'DATA_IMPORT_CATALOG_REGISTERED'\n    DATA_IMPORT_REPORT_CREATED = 'DATA_IMPORT_REPORT_CREATED'", 1)
        audit_path.write_text(content)
