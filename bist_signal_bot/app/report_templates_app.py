from pathlib import Path
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
