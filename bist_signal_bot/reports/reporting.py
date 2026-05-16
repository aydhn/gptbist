import pandas as pd
from typing import Any
from bist_signal_bot.reports.models import GeneratedReport, TelegramDigest, ReportSection

def generated_report_to_dict(report: GeneratedReport) -> dict[str, Any]:
    return report.safe_public_dict()

def telegram_digest_to_dict(digest: TelegramDigest) -> dict[str, Any]:
    return digest.model_dump()

def report_sections_to_dataframe(sections: list[ReportSection]) -> pd.DataFrame:
    return pd.DataFrame([s.model_dump() for s in sections])

def format_generated_report_text(report: GeneratedReport) -> str:
    from bist_signal_bot.reports.templates import ReportTemplateRenderer
    return ReportTemplateRenderer().render_text(report)

def format_telegram_digest_text(digest: TelegramDigest) -> str:
    return digest.message

def format_report_summary_markdown(report: GeneratedReport) -> str:
    return f"# {report.title}\n{report.status.value}\n{report.disclaimer}"
