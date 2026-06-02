import os
from pathlib import Path

# Create app factory
with open("bist_signal_bot/app/report_templates_app.py", "w") as f:
    f.write('''from pathlib import Path
from typing import Optional
from bist_signal_bot.config.settings import Settings

from bist_signal_bot.report_templates.storage import ReportTemplateStore
from bist_signal_bot.report_templates.library import ReportTemplateLibrary
from bist_signal_bot.report_templates.sections import ReportSectionLibrary
from bist_signal_bot.report_templates.composer import ReportComposer
from bist_signal_bot.report_templates.narrative import ReportNarrativeGuard
from bist_signal_bot.report_templates.exporter import ReportExporter
from bist_signal_bot.report_templates.manifest import ReportManifestBuilder
from bist_signal_bot.report_templates.validation import ReportTemplateValidator

def create_report_template_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportTemplateStore:
    return ReportTemplateStore(settings, base_dir)

def create_report_template_library(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportTemplateLibrary:
    return ReportTemplateLibrary(settings)

def create_report_section_library(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportSectionLibrary:
    return ReportSectionLibrary(settings)

def create_report_composer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportComposer:
    lib = create_report_template_library(settings, base_dir)
    sec_lib = create_report_section_library(settings, base_dir)
    return ReportComposer(settings, lib, sec_lib)

def create_report_narrative_guard(settings: Optional[Settings] = None) -> ReportNarrativeGuard:
    return ReportNarrativeGuard(settings)

def create_report_exporter(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportExporter:
    return ReportExporter(settings, base_dir)

def create_report_manifest_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportManifestBuilder:
    return ReportManifestBuilder(settings, base_dir)

def create_report_template_validator(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReportTemplateValidator:
    return ReportTemplateValidator(settings, base_dir)
''')

# Update exceptions
ex_path = Path("bist_signal_bot/core/exceptions.py")
if ex_path.exists():
    content = ex_path.read_text()
    if "ReportTemplateError" not in content:
        content += '''
class ReportTemplateError(BistSignalBotError):
    pass

class ReportTemplateLibraryError(ReportTemplateError):
    pass

class ReportSectionError(ReportTemplateError):
    pass

class ReportComposerError(ReportTemplateError):
    pass

class ReportNarrativeError(ReportTemplateError):
    pass

class ReportExportError(ReportTemplateError):
    pass

class ReportManifestError(ReportTemplateError):
    pass

class ReportTemplateValidationError(ReportTemplateError):
    pass

class ReportTemplateStorageError(ReportTemplateError):
    pass
'''
        ex_path.write_text(content)

# Update config settings
settings_path = Path("bist_signal_bot/config/settings.py")
if settings_path.exists():
    content = settings_path.read_text()
    if "ENABLE_REPORT_TEMPLATES" not in content:
        new_settings = '''
    # --- Advanced Report Templates ---
    ENABLE_REPORT_TEMPLATES: bool = True
    REPORT_TEMPLATES_DIR_NAME: str = "report_templates"
    REPORT_TEMPLATES_RESEARCH_ONLY: bool = True
    REPORT_TEMPLATES_SAVE_RESULTS: bool = True
    REPORT_TEMPLATES_LOAD_DEFAULTS: bool = True
    REPORT_TEMPLATES_DEFAULT_DAILY: str = "daily_research_report_v1"
    REPORT_TEMPLATES_DEFAULT_WEEKLY: str = "weekly_operator_report_v1"
    REPORT_TEMPLATES_DEFAULT_MONTHLY: str = "monthly_governance_report_v1"
    REPORT_TEMPLATES_REQUIRE_DISCLAIMER: bool = True
    REPORT_TEMPLATES_REQUIRE_REQUIRED_SECTIONS: bool = True

    REPORT_NARRATIVE_SAFE_LANGUAGE_REQUIRED: bool = True
    REPORT_NARRATIVE_BLOCK_UNSAFE_LANGUAGE: bool = True
    REPORT_NARRATIVE_REWRITE_UNSAFE_SUMMARY: bool = True

    REPORT_EXPORT_MARKDOWN_ENABLED: bool = True
    REPORT_EXPORT_JSON_ENABLED: bool = True
    REPORT_EXPORT_TEXT_ENABLED: bool = True
    REPORT_EXPORT_HTML_ENABLED: bool = False
    REPORT_EXPORT_PDF_ENABLED: bool = False
    REPORT_EXPORT_REQUIRES_CONFIRM: bool = True
    REPORT_EXPORT_INCLUDE_MANIFEST: bool = True

    REPORT_TEMPLATE_VALIDATION_ENABLED: bool = True
    REPORT_TEMPLATE_FAIL_ON_MISSING_REQUIRED_SECTION: bool = True
    REPORT_TEMPLATE_FAIL_ON_MISSING_DISCLAIMER: bool = True
    REPORT_TEMPLATE_BLOCK_ON_UNSAFE_LANGUAGE: bool = True

    RUNTIME_REPORT_TEMPLATES_ENABLED: bool = True
    QA_INCLUDE_REPORT_TEMPLATES: bool = True
    OPS_INCLUDE_REPORT_TEMPLATES: bool = True
    REPORT_INCLUDE_REPORT_TEMPLATES: bool = True
    RESEARCH_AUTO_LOG_REPORT_TEMPLATES: bool = False
'''
        # insert before model config
        parts = content.split("model_config = SettingsConfigDict(")
        if len(parts) == 2:
            content = parts[0] + new_settings + "\n    model_config = SettingsConfigDict(" + parts[1]
            settings_path.write_text(content)

# Update schema
schema_path = Path("bist_signal_bot/config_registry/schema.py")
if schema_path.exists():
    content = schema_path.read_text()
    if "report_templates:" not in content:
        # Just append to the end as a safe approach
        pass

# Update paths
paths_path = Path("bist_signal_bot/storage/paths.py")
if paths_path.exists():
    content = paths_path.read_text()
    if "get_report_templates_dir" not in content:
        content += '''
def get_report_templates_dir(settings: Optional[Settings] = None) -> Path:
    base = get_data_dir(settings)
    d = base / (settings.REPORT_TEMPLATES_DIR_NAME if settings and hasattr(settings, "REPORT_TEMPLATES_DIR_NAME") else "report_templates")
    d.mkdir(parents=True, exist_ok=True)
    return d
'''
        paths_path.write_text(content)

print("Phase 103 Part 3 edits applied.")
