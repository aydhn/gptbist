import dataclasses
# import pandas as pd
from typing import Any
from bist_signal_bot.financials.models import (
    FinancialStatementRecord,
    NormalizedFinancialStatement,
    FinancialRatio,
    FinancialTrendMetric,
    EarningsQualityAssessment,
    SectorFinancialComparison,
    FinancialImportResult,
    FinancialAnalysisReport
)

def statement_record_to_dict(record: FinancialStatementRecord) -> dict[str, Any]:
    return dataclasses.asdict(record)

def normalized_statement_to_dict(statement: NormalizedFinancialStatement) -> dict[str, Any]:
    return dataclasses.asdict(statement)

def ratio_to_dict(ratio: FinancialRatio) -> dict[str, Any]:
    return dataclasses.asdict(ratio)

def trend_to_dict(trend: FinancialTrendMetric) -> dict[str, Any]:
    return dataclasses.asdict(trend)

def quality_to_dict(assessment: EarningsQualityAssessment) -> dict[str, Any]:
    return dataclasses.asdict(assessment)

def sector_comparison_to_dict(comparison: SectorFinancialComparison) -> dict[str, Any]:
    return dataclasses.asdict(comparison)

def import_result_to_dict(result: FinancialImportResult) -> dict[str, Any]:
    return dataclasses.asdict(result)

def analysis_report_to_dict(report: FinancialAnalysisReport) -> dict[str, Any]:
    return dataclasses.asdict(report)

def statements_to_dataframe(statements: list[NormalizedFinancialStatement]) -> 'pd.DataFrame':
    if not statements:
        return [] # pd.DataFrame()
    return [dataclasses.asdict(s) for s in statements] # pd.DataFrame

def ratios_to_dataframe(ratios: list[FinancialRatio]) -> 'pd.DataFrame':
    if not ratios:
        return [] # pd.DataFrame()
    return [dataclasses.asdict(r) for r in ratios] # pd.DataFrame

def trends_to_dataframe(trends: list[FinancialTrendMetric]) -> 'pd.DataFrame':
    if not trends:
        return [] # pd.DataFrame()
    return [dataclasses.asdict(t) for t in trends] # pd.DataFrame

def format_statement_text(statement: NormalizedFinancialStatement) -> str:
    return f"Statement: {statement.symbol} {statement.fiscal_year} {statement.fiscal_period}"

def format_ratios_text(ratios: list[FinancialRatio]) -> str:
    return f"Ratios for {len(ratios)} metrics"

def format_quality_text(assessment: EarningsQualityAssessment) -> str:
    return f"Quality: {assessment.status} Score: {assessment.overall_quality_score}"

def format_sector_comparison_text(comparison: SectorFinancialComparison) -> str:
    return f"Sector Score: {comparison.sector_score}"

def format_financial_analysis_report_markdown(report: FinancialAnalysisReport) -> str:
    md = f"# Financial Analysis Report\n\n"
    if report.symbol:
        md += f"Symbol: {report.symbol}\n"
    md += f"Generated: {report.generated_at.isoformat()}\n\n"

    if report.warnings:
        md += "## Warnings\n"
        for w in report.warnings:
            md += f"- {w}\n"
        md += "\n"

    md += "## Key Findings\n"
    for f in report.key_findings:
        md += f"- {f}\n"
    md += "\n"

    md += f"*{report.disclaimer}*\n"
    return md
