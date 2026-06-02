import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.report_templates.models import (
    ReportTemplate, ReportSectionDefinition, ComposedReport, ReportExportPack,
    ReportManifest, ReportTemplateValidationResult, ReportTemplatesReport, ReportTemplateKind
)
from bist_signal_bot.storage.paths import get_report_templates_dir

class ReportTemplateStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir or get_report_templates_dir(settings)
        self.templates_file = self.base_dir / "templates" / "report_templates.json"
        self.sections_file = self.base_dir / "sections" / "report_sections.json"
        self.composed_file = self.base_dir / "composed" / "composed_reports.jsonl"
        self.exports_file = self.base_dir / "exports" / "report_export_packs.jsonl"
        self.manifests_file = self.base_dir / "manifests" / "report_manifests.jsonl"
        self.validations_file = self.base_dir / "validations" / "report_template_validations.jsonl"

        for p in [self.templates_file, self.sections_file, self.composed_file, self.exports_file, self.manifests_file, self.validations_file]:
            p.parent.mkdir(parents=True, exist_ok=True)

    def save_templates(self, templates: List[ReportTemplate]) -> Path:
        data = [t.model_dump(mode="json") for t in templates]
        with open(self.templates_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.templates_file

    def load_templates(self) -> List[ReportTemplate]:
        if not self.templates_file.exists():
            return []
        with open(self.templates_file, "r") as f:
            data = json.load(f)
        return [ReportTemplate(**d) for d in data]

    def save_sections(self, sections: List[ReportSectionDefinition]) -> Path:
        data = [s.model_dump(mode="json") for s in sections]
        with open(self.sections_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.sections_file

    def load_sections(self) -> List[ReportSectionDefinition]:
        if not self.sections_file.exists():
            return []
        with open(self.sections_file, "r") as f:
            data = json.load(f)
        return [ReportSectionDefinition(**d) for d in data]

    def append_composed_report(self, report: ComposedReport) -> Path:
        with open(self.composed_file, "a") as f:
            f.write(json.dumps(report.model_dump(mode="json")) + "\n")
        return self.composed_file

    def load_composed_reports(self, limit: int = 1000) -> List[ComposedReport]:
        if not self.composed_file.exists():
            return []
        reports = []
        with open(self.composed_file, "r") as f:
            for line in f:
                if line.strip():
                    reports.append(ComposedReport(**json.loads(line)))
        return reports[-limit:]

    def load_latest_composed_report(self, kind: Optional[ReportTemplateKind] = None) -> Optional[ComposedReport]:
        reports = self.load_composed_reports()
        if kind:
            reports = [r for r in reports if r.kind == kind]
        return reports[-1] if reports else None

    def append_export_pack(self, pack: ReportExportPack) -> Path:
        with open(self.exports_file, "a") as f:
            f.write(json.dumps(pack.model_dump(mode="json")) + "\n")
        return self.exports_file

    def append_manifest(self, manifest: ReportManifest) -> Path:
        with open(self.manifests_file, "a") as f:
            f.write(json.dumps(manifest.model_dump(mode="json")) + "\n")
        return self.manifests_file

    def append_validation(self, result: ReportTemplateValidationResult) -> Path:
        with open(self.validations_file, "a") as f:
            f.write(json.dumps(result.model_dump(mode="json")) + "\n")
        return self.validations_file

    def save_report(self, report: ReportTemplatesReport, markdown_text: str) -> Dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "report_templates_report.md"
        json_path = report_dir / "report_templates_report.json"

        with open(md_path, "w") as f:
            f.write(markdown_text)
        with open(json_path, "w") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2)

        return {"markdown": md_path, "json": json_path}
