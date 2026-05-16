from typing import Any
import json
from bist_signal_bot.reports.models import GeneratedReport

class ReportTemplateRenderer:
    def render_markdown(self, report: GeneratedReport) -> str:
        lines = [f"# {report.title}", f"**Generated At:** {report.generated_at.isoformat()}", "", f"*{report.disclaimer}*", ""]
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append(section.body_markdown)
            if section.summary:
                lines.append(f"```json\n{json.dumps(section.summary, indent=2)}\n```")
            lines.append("")
        return "\n".join(lines)

    def render_text(self, report: GeneratedReport) -> str:
        return self.render_markdown(report) # Simplification for now

    def render_html(self, report: GeneratedReport) -> str:
        md = self.render_markdown(report)
        return f"<html><body><pre>{md}</pre></body></html>"

    def render_json(self, report: GeneratedReport) -> dict[str, Any]:
        return report.safe_public_dict()

    def render_csv_tables(self, report: GeneratedReport) -> dict[str, list[dict[str, Any]]]:
        csv_tables = {}
        for section in report.sections:
            for table_name, table_data in section.tables.items():
                csv_tables[f"{section.section_id}_{table_name}"] = table_data
        return csv_tables
