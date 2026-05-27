import uuid
from typing import Any
from bist_signal_bot.financials.models import (
    FinancialStatementRecord,
    NormalizedFinancialStatement,
    FinancialPeriodType
)

class FinancialStatementNormalizer:
    def __init__(self, settings=None):
        self.settings = settings
        self.synonyms = {
            "revenue": ["revenue", "net sales", "satış gelirleri", "hasılat"],
            "gross_profit": ["gross profit", "brüt kar", "brüt kâr"],
            "operating_profit": ["operating profit", "faaliyet karı", "esas faaliyet kârı"],
            "ebitda": ["ebitda", "favök"],
            "net_income": ["net income", "net dönem karı", "net kâr"],
            "total_assets": ["total assets", "toplam varlıklar", "aktif toplamı"],
            "total_equity": ["total equity", "equity", "özkaynaklar", "toplam özkaynaklar"],
            "total_debt": ["total debt", "debt", "finansal borçlar", "kısa ve uzun vadeli borçlar"],
            "cash_and_equivalents": ["cash and equivalents", "cash", "nakit ve nakit benzerleri"],
            "operating_cash_flow": ["operating cash flow", "işletme faaliyetlerinden nakit akışı"],
            "capex": ["capex", "capital expenditure", "yatırım harcamaları"]
        }

    def normalize_records(self, records: list[FinancialStatementRecord]) -> list[NormalizedFinancialStatement]:
        groups = {}
        for r in records:
            key = (r.symbol, r.fiscal_year, r.fiscal_period)
            if key not in groups:
                groups[key] = []
            groups[key].append(r)

        results = []
        for key, recs in groups.items():
            results.append(self.normalize_symbol_period(key[0], key[1], key[2], recs))
        return results

    def normalize_symbol_period(self, symbol: str, fiscal_year: int, fiscal_period: str, records: list[FinancialStatementRecord]) -> NormalizedFinancialStatement:
        values = {}
        source_records = []
        period_end = None
        currency = "TRY"
        reported_at = None
        period_type = FinancialPeriodType.UNKNOWN

        for r in records:
            source_records.append(r.record_id)
            if r.period_end:
                period_end = r.period_end
            if r.currency:
                currency = r.currency
            if r.reported_at:
                reported_at = r.reported_at
            if r.period_type != FinancialPeriodType.UNKNOWN:
                period_type = r.period_type

            for k, v in r.values.items():
                mapped_k = self.map_item_name(k)
                if mapped_k:
                    values[mapped_k] = self.coerce_numeric(v)
                else:
                    values[k] = self.coerce_numeric(v) # Try direct mapping

        # Construct NormalizedFinancialStatement
        statement = NormalizedFinancialStatement(
            normalized_id=str(uuid.uuid4()),
            symbol=symbol,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            period_type=period_type,
            period_end=period_end, # type: ignore
            currency=currency,
            source_records=source_records,
            warnings=[],
            metadata={},
            reported_at=reported_at,
            revenue=values.get("revenue"),
            gross_profit=values.get("gross_profit"),
            operating_profit=values.get("operating_profit"),
            ebitda=values.get("ebitda"),
            net_income=values.get("net_income"),
            total_assets=values.get("total_assets"),
            total_equity=values.get("total_equity"),
            total_debt=values.get("total_debt"),
            cash_and_equivalents=values.get("cash_and_equivalents"),
            operating_cash_flow=values.get("operating_cash_flow"),
            capex=values.get("capex")
        )

        warnings = self.validate_normalized(statement)
        statement.warnings.extend(warnings)

        return statement

    def map_item_name(self, item_name: str) -> str | None:
        item_lower = item_name.lower().strip()
        for key, synonyms_list in self.synonyms.items():
            if item_lower in [s.lower() for s in synonyms_list]:
                return key
        return None

    def coerce_numeric(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return float(value)
        except (ValueError, TypeError):
            return None

    def validate_normalized(self, statement: NormalizedFinancialStatement) -> list[str]:
        warnings = []
        essential_fields = ["revenue", "net_income", "total_assets", "total_equity"]
        for field in essential_fields:
            if getattr(statement, field) is None:
                warnings.append(f"Missing essential field: {field}")
        return warnings
