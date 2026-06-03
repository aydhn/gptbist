import json
from typing import Any
from bist_signal_bot.markets.models import (
    MarketDefinition, InstrumentDefinition, SymbolMapping, MarketCalendarDay,
    MarketSession, CurrencyDefinition, MarketUniverse, MarketNormalizationResult,
    MarketValidationResult, MarketGovernanceAssessment, MarketRegistryReport
)

def market_to_dict(market: MarketDefinition) -> dict[str, Any]:
    return json.loads(market.model_dump_json())

def instrument_to_dict(instrument: InstrumentDefinition) -> dict[str, Any]:
    return json.loads(instrument.model_dump_json())

def symbol_mapping_to_dict(mapping: SymbolMapping) -> dict[str, Any]:
    return json.loads(mapping.model_dump_json())

def calendar_day_to_dict(day: MarketCalendarDay) -> dict[str, Any]:
    return json.loads(day.model_dump_json())

def session_to_dict(session: MarketSession) -> dict[str, Any]:
    return json.loads(session.model_dump_json())

def currency_to_dict(currency: CurrencyDefinition) -> dict[str, Any]:
    return json.loads(currency.model_dump_json())

def universe_to_dict(universe: MarketUniverse) -> dict[str, Any]:
    return json.loads(universe.model_dump_json())

def normalization_to_dict(result: MarketNormalizationResult) -> dict[str, Any]:
    return json.loads(result.model_dump_json())

def validation_to_dict(result: MarketValidationResult) -> dict[str, Any]:
    return json.loads(result.model_dump_json())

def governance_to_dict(assessment: MarketGovernanceAssessment) -> dict[str, Any]:
    return json.loads(assessment.model_dump_json())

def report_to_dict(report: MarketRegistryReport) -> dict[str, Any]:
    return json.loads(report.model_dump_json())

def format_market_text(market: MarketDefinition) -> str:
    return f"Market: {market.market_id} | Name: {market.name} | Type: {market.market_type.value} | Status: {market.status.value}\nDisclaimer: {market.disclaimer}"

def format_instrument_text(instrument: InstrumentDefinition) -> str:
    return f"Instrument: {instrument.canonical_symbol} | Market: {instrument.market_id} | Asset Class: {instrument.asset_class.value}\nDisclaimer: {instrument.disclaimer}"

def format_universe_text(universe: MarketUniverse) -> str:
    return f"Universe: {universe.name} | Market: {universe.market_id} | Symbols: {len(universe.symbols)}\nDisclaimer: {universe.disclaimer}"

def format_validation_text(result: MarketValidationResult) -> str:
    return f"Validation: {result.market_id} | Status: {result.status.value} | Findings: {len(result.findings)}\nDisclaimer: {result.disclaimer}"

def format_market_registry_report_markdown(report: MarketRegistryReport) -> str:
    lines = [
        f"# Market Registry Report",
        f"Generated: {report.generated_at.isoformat()}",
        "",
        "## Markets",
        *[f"- {m.market_id}: {m.name} ({m.status.value})" for m in report.markets],
        "",
        "## Universes",
        *[f"- {u.name} ({len(u.symbols)} symbols)" for u in report.universes],
        "",
        "## Governance",
        *[f"- {g.market_id}: {g.status.value}" for g in report.governance_assessments],
        "",
        "## Disclaimer",
        report.disclaimer
    ]
    return "\n".join(lines)
