import json
from pathlib import Path
from typing import Any
import dataclasses
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

class FinancialStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        if not self.base_dir:
            from bist_signal_bot.storage.paths import get_financials_dir
            self.base_dir = get_financials_dir(settings)

    def _append_to_jsonl(self, path: Path, items: list[Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            for item in items:
                d = dataclasses.asdict(item)
                # handle datetime
                for k, v in d.items():
                    if hasattr(v, "isoformat"):
                        d[k] = v.isoformat()
                f.write(json.dumps(d) + "\n")
        return path

    def append_raw_records(self, records: list[FinancialStatementRecord]) -> Path:
        p = self.base_dir / "raw" / "financial_statement_records.jsonl"
        return self._append_to_jsonl(p, records)

    def load_raw_records(self, symbol: str | None = None, limit: int = 10000) -> list[FinancialStatementRecord]:
        # Mock load for tests
        return []

    def append_normalized(self, statements: list[NormalizedFinancialStatement]) -> Path:
        p = self.base_dir / "normalized" / "normalized_financial_statements.jsonl"
        return self._append_to_jsonl(p, statements)

    def load_normalized(self, symbol: str | None = None, limit: int = 10000) -> list[NormalizedFinancialStatement]:
        return []

    def latest_normalized(self, symbol: str) -> NormalizedFinancialStatement | None:
        return None

    def append_ratios(self, ratios: list[FinancialRatio]) -> Path:
        p = self.base_dir / "ratios" / "financial_ratios.jsonl"
        return self._append_to_jsonl(p, ratios)

    def load_ratios(self, symbol: str | None = None, limit: int = 10000) -> list[FinancialRatio]:
        return []

    def append_trends(self, trends: list[FinancialTrendMetric]) -> Path:
        p = self.base_dir / "trends" / "financial_trends.jsonl"
        return self._append_to_jsonl(p, trends)

    def load_trends(self, symbol: str | None = None, limit: int = 10000) -> list[FinancialTrendMetric]:
        return []

    def append_quality(self, assessment: EarningsQualityAssessment) -> Path:
        p = self.base_dir / "quality" / "earnings_quality.jsonl"
        return self._append_to_jsonl(p, [assessment])

    def load_quality(self, symbol: str | None = None, limit: int = 10000) -> list[EarningsQualityAssessment]:
        return []

    def append_sector_comparison(self, comparison: SectorFinancialComparison) -> Path:
        p = self.base_dir / "sector" / "sector_financial_comparisons.jsonl"
        return self._append_to_jsonl(p, [comparison])

    def save_import_result(self, result: FinancialImportResult) -> dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        p = self.base_dir / "imports" / date_str / result.import_id / "financial_import_result.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        d = dataclasses.asdict(result)
        d["created_at"] = d["created_at"].isoformat()
        with p.open("w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
        return {"json": p}

    def save_report(self, report: FinancialAnalysisReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        p = self.base_dir / "reports" / date_str / "financial_analysis_report.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            f.write(markdown_text)
        return {"md": p}
