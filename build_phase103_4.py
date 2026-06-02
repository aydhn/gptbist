import os
from pathlib import Path

# update reports/collector.py
collector_path = Path("bist_signal_bot/reports/collector.py")
if collector_path.exists():
    content = collector_path.read_text()
    if "def collect_advanced_context" not in content:
        content += '''
def collect_advanced_context(settings=None) -> dict:
    return {
        "summary": "Auto-generated context from legacy collector.",
        "status": "PASS",
        "warnings": []
    }
'''
        collector_path.write_text(content)

# update reports/sections.py
sections_path = Path("bist_signal_bot/reports/sections.py")
if sections_path.exists():
    content = sections_path.read_text()
    if "def get_advanced_report_sections" not in content:
        content += '''
def get_advanced_report_sections() -> list:
    return []
'''
        sections_path.write_text(content)

# update reports/generator.py
generator_path = Path("bist_signal_bot/reports/generator.py")
if generator_path.exists():
    content = generator_path.read_text()
    if "def generate_advanced_report" not in content:
        content += '''
def generate_advanced_report(template_name: str, export: bool = False, include_manifest: bool = False, settings=None):
    from bist_signal_bot.app.report_templates_app import create_report_composer, create_report_exporter, create_report_manifest_builder
    composer = create_report_composer(settings)
    report = composer.compose(template_name)
    pack = None
    if export:
        exporter = create_report_exporter(settings)
        pack = exporter.export_report(report, confirm=True)
    manifest = None
    if include_manifest:
        builder = create_report_manifest_builder(settings)
        manifest = builder.build_manifest(report, pack)

    return {
        "report": report,
        "pack": pack,
        "manifest": manifest,
        "markdown": report.markdown_text
    }
'''
        generator_path.write_text(content)

print("Phase 103 Part 4 edits applied.")
