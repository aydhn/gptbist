import pandas as pd
from typing import Any
from bist_signal_bot.docs.models import DocsValidationReport, DocsGenerationResult, DocsValidationFinding, CLICommandDoc

def docs_validation_report_to_dict(report: DocsValidationReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def docs_generation_result_to_dict(result: DocsGenerationResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def docs_findings_to_dataframe(findings: list[DocsValidationFinding]) -> pd.DataFrame:
    if not findings:
        return pd.DataFrame()
    return pd.DataFrame([f.model_dump() for f in findings])

def command_catalog_to_dataframe(commands: list[CLICommandDoc]) -> pd.DataFrame:
    if not commands:
        return pd.DataFrame()
    return pd.DataFrame([c.model_dump() for c in commands])

def format_docs_validation_text(report: DocsValidationReport) -> str:
    return f"Status: {report.status.value}\nChecked Files: {report.checked_files}\nFindings: {len(report.findings)}"

def format_docs_generation_text(result: DocsGenerationResult) -> str:
    return f"Status: {result.status.value}\nPages Created: {result.pages_created}"

def format_docs_validation_markdown(report: DocsValidationReport) -> str:
    return f"# Validation Report\n\nStatus: {report.status.value}\n"
