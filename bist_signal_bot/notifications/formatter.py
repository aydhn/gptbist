# Phase 107 added formatters
def format_market_definition(market) -> str:
    return f"Market: {market.market_id}\nStatus: {market.status.value}\nDisclaimer: Local metadata only."

def format_instrument_definition(instrument) -> str:
    return f"Instrument: {instrument.canonical_symbol}\nDisclaimer: Local metadata only."

def format_market_universe(universe) -> str:
    return f"Universe: {universe.name}\nSymbols: {len(universe.symbols)}\nDisclaimer: Local metadata only."

def format_market_validation(result) -> str:
    return f"Validation for {result.market_id}\nStatus: {result.status.value}\nDisclaimer: Local metadata only."

def format_market_governance(assessment) -> str:
    return f"Governance for {assessment.market_id}\nStatus: {assessment.status.value}\nDisclaimer: Local metadata only."

def format_market_registry_report(report) -> str:
    return f"Market Registry Report\nMarkets: {len(report.markets)}\nDisclaimer: Local metadata only."

def format_maintenance_summary(run) -> str:
    return "BIST Bot Maintenance Automation Özeti\nBu çıktı yerel yazılım bakım özetidir.\nYatırım tavsiyesi değildir.\nİşlem uygunluğu anlamına gelmez.\nGerçek emir gönderilmedi."
