import os
from pathlib import Path

# Data Catalog
os.makedirs("bist_signal_bot/data_catalog", exist_ok=True)
Path("bist_signal_bot/data_catalog/__init__.py").touch()
for f in ["registry.py", "profiler.py", "quality.py", "provenance.py", "lineage.py"]:
    if not Path(f"bist_signal_bot/data_catalog/{f}").exists():
        Path(f"bist_signal_bot/data_catalog/{f}").write_text("# Phase 93/102 Data Catalog Placeholder\n")

# Feature Store
os.makedirs("bist_signal_bot/feature_store", exist_ok=True)
Path("bist_signal_bot/feature_store/__init__.py").touch()
if not Path("bist_signal_bot/feature_store/computation.py").exists():
    Path("bist_signal_bot/feature_store/computation.py").write_text("# Phase 94/102 Feature Store Placeholder\n")

# Performance
os.makedirs("bist_signal_bot/performance", exist_ok=True)
Path("bist_signal_bot/performance/__init__.py").touch()
for f in ["cache.py", "benchmark.py"]:
    if not Path(f"bist_signal_bot/performance/{f}").exists():
        Path(f"bist_signal_bot/performance/{f}").write_text("# Phase 101/102 Performance Placeholder\n")

# Reports
os.makedirs("bist_signal_bot/reports", exist_ok=True)
Path("bist_signal_bot/reports/__init__.py").touch()
for f in ["collector.py", "sections.py"]:
    if not Path(f"bist_signal_bot/reports/{f}").exists():
         Path(f"bist_signal_bot/reports/{f}").write_text("# Phase 102 Reports Placeholder\n")

# Security
os.makedirs("bist_signal_bot/security", exist_ok=True)
Path("bist_signal_bot/security/__init__.py").touch()
for f in ["path_guard.py", "redaction.py", "claims_guard.py"]:
    if not Path(f"bist_signal_bot/security/{f}").exists():
         if f == "path_guard.py":
             Path(f"bist_signal_bot/security/{f}").write_text("""
from pathlib import Path
class PathGuard:
    @staticmethod
    def ensure_safe_path(path: Path, base_dir: Path | None = None) -> None:
        p_str = str(path)
        if ".." in p_str:
            raise ValueError("Path traversal attempt")
        if base_dir:
            try:
                path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                raise ValueError("Path outside base_dir")
""")
         else:
             Path(f"bist_signal_bot/security/{f}").write_text("# Phase 102 Security Placeholder\n")

# Settings update
settings_path = Path("bist_signal_bot/config/settings.py")
if settings_path.exists():
    content = settings_path.read_text()
    if "ENABLE_DATA_IMPORT" not in content:
        content += """
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
        settings_path.write_text(content)

# Notifications
os.makedirs("bist_signal_bot/notifications", exist_ok=True)
Path("bist_signal_bot/notifications/__init__.py").touch()
if not Path("bist_signal_bot/notifications/formatter.py").exists():
    Path("bist_signal_bot/notifications/formatter.py").write_text("# Phase 102 Notifications Formatter Placeholder\n")

# Other dirs
for d in ["qa", "ops", "docs_hub", "final_handoff", "maintenance", "app", "governance", "config_registry", "cli"]:
    os.makedirs(f"bist_signal_bot/{d}", exist_ok=True)
    Path(f"bist_signal_bot/{d}/__init__.py").touch()

for f in ["qa/release_gate.py", "ops/readiness.py", "docs_hub/coverage.py", "final_handoff/operator_playbook.py",
          "maintenance/doctor.py", "app/healthcheck.py", "governance/gate.py", "config_registry/schema.py",
          "cli/commands.py", "cli/parsers.py", "cli/formatting.py"]:
     if not Path(f"bist_signal_bot/{f}").exists():
         Path(f"bist_signal_bot/{f}").write_text(f"# Phase 102 {f} Placeholder\n")
