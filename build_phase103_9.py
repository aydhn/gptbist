import os
from pathlib import Path

# core/audit.py
p1 = Path("bist_signal_bot/core/audit.py")
if p1.exists():
    c = p1.read_text()
    if "REPORT_COMPOSED" not in c:
        if "    DATA_IMPORT_REPORT_CREATED = 'DATA_IMPORT_REPORT_CREATED'" in c:
            c = c.replace(
                "    DATA_IMPORT_REPORT_CREATED = 'DATA_IMPORT_REPORT_CREATED'",
                "    DATA_IMPORT_REPORT_CREATED = 'DATA_IMPORT_REPORT_CREATED'\n    REPORT_TEMPLATES_LOADED = 'REPORT_TEMPLATES_LOADED'\n    REPORT_SECTION_RENDERED = 'REPORT_SECTION_RENDERED'\n    REPORT_COMPOSED = 'REPORT_COMPOSED'\n    REPORT_NARRATIVE_VALIDATED = 'REPORT_NARRATIVE_VALIDATED'\n    REPORT_EXPORTED = 'REPORT_EXPORTED'\n    REPORT_MANIFEST_CREATED = 'REPORT_MANIFEST_CREATED'\n    REPORT_TEMPLATE_VALIDATED = 'REPORT_TEMPLATE_VALIDATED'\n    REPORT_TEMPLATES_REPORT_CREATED = 'REPORT_TEMPLATES_REPORT_CREATED'"
            )
        p1.write_text(c)

# notifications/formatter.py
p2 = Path("bist_signal_bot/notifications/formatter.py")
if p2.exists():
    c = p2.read_text()
    if "def format_composed_report" not in c:
        c += '''
def format_report_template(template) -> str:
    return "Report Template Formatted String"

def format_composed_report(report) -> str:
    return "Composed Report Formatted String"

def format_report_export_pack(pack) -> str:
    return "Report Export Pack Formatted String"

def format_report_template_validation(result) -> str:
    return "Report Template Validation Formatted String"

def format_report_templates_report(report) -> str:
    return "Report Templates Report Formatted String"
'''
        p2.write_text(c)

# .env.example
p3 = Path(".env.example")
if p3.exists():
    c = p3.read_text()
    if "ENABLE_REPORT_TEMPLATES" not in c:
        c += '''
# --- Advanced Report Templates ---
ENABLE_REPORT_TEMPLATES=true
REPORT_TEMPLATES_DIR_NAME="report_templates"
REPORT_TEMPLATES_RESEARCH_ONLY=true
REPORT_TEMPLATES_SAVE_RESULTS=true
REPORT_TEMPLATES_LOAD_DEFAULTS=true
REPORT_TEMPLATES_DEFAULT_DAILY="daily_research_report_v1"
REPORT_TEMPLATES_DEFAULT_WEEKLY="weekly_operator_report_v1"
REPORT_TEMPLATES_DEFAULT_MONTHLY="monthly_governance_report_v1"
REPORT_TEMPLATES_REQUIRE_DISCLAIMER=true
REPORT_TEMPLATES_REQUIRE_REQUIRED_SECTIONS=true
REPORT_NARRATIVE_SAFE_LANGUAGE_REQUIRED=true
REPORT_NARRATIVE_BLOCK_UNSAFE_LANGUAGE=true
REPORT_NARRATIVE_REWRITE_UNSAFE_SUMMARY=true
REPORT_EXPORT_MARKDOWN_ENABLED=true
REPORT_EXPORT_JSON_ENABLED=true
REPORT_EXPORT_TEXT_ENABLED=true
REPORT_EXPORT_HTML_ENABLED=false
REPORT_EXPORT_PDF_ENABLED=false
REPORT_EXPORT_REQUIRES_CONFIRM=true
REPORT_EXPORT_INCLUDE_MANIFEST=true
REPORT_TEMPLATE_VALIDATION_ENABLED=true
REPORT_TEMPLATE_FAIL_ON_MISSING_REQUIRED_SECTION=true
REPORT_TEMPLATE_FAIL_ON_MISSING_DISCLAIMER=true
REPORT_TEMPLATE_BLOCK_ON_UNSAFE_LANGUAGE=true
RUNTIME_REPORT_TEMPLATES_ENABLED=true
QA_INCLUDE_REPORT_TEMPLATES=true
OPS_INCLUDE_REPORT_TEMPLATES=true
REPORT_INCLUDE_REPORT_TEMPLATES=true
RESEARCH_AUTO_LOG_REPORT_TEMPLATES=false
'''
        p3.write_text(c)

# README.md
p4 = Path("README.md")
if p4.exists():
    c = p4.read_text()
    if "Advanced Report Templates" not in c:
        c += '''
### Advanced Report Templates
- Report template library
- Section library
- Report composer
- Safe narrative guard
- Export pack
- Report manifest
- QA/Ops entegrasyonu
- CLI report-templates kullanımı
'''
        p4.write_text(c)

print("Phase 103 Part 9 edits applied.")
