from typing import Optional, List
from bist_signal_bot.markets.models import MarketDefinition, MarketStatus, MarketType, ExchangeRegion, QuoteConvention

class MarketRegistry:
    def __init__(self, store=None):
        self.store = store
        self._markets = {}
        if self.store:
            for m in self.store.load_markets():
                self._markets[m.market_id] = m

    def default_markets(self) -> List[MarketDefinition]:
        return [
            MarketDefinition(
                market_id="BIST_EQUITY",
                name="Borsa Istanbul Equities",
                market_type=MarketType.EQUITY,
                region=ExchangeRegion.TURKIYE,
                default_currency="TRY",
                timezone="Europe/Istanbul",
                exchange_code="BIST",
                quote_convention=QuoteConvention.PRICE,
                status=MarketStatus.ACTIVE,
                metadata={"description": "Borsa Istanbul Equity Market"}
            ),
            MarketDefinition(
                market_id="US_EQUITY_RESEARCH",
                name="US Equities Research",
                market_type=MarketType.EQUITY,
                region=ExchangeRegion.US,
                default_currency="USD",
                timezone="America/New_York",
                exchange_code="US",
                quote_convention=QuoteConvention.PRICE,
                status=MarketStatus.WATCH,
                metadata={"description": "US Equity Market Research Data"}
            ),
            MarketDefinition(
                market_id="GLOBAL_INDEX_RESEARCH",
                name="Global Indices",
                market_type=MarketType.INDEX,
                region=ExchangeRegion.GLOBAL,
                default_currency="USD",
                timezone="UTC",
                quote_convention=QuoteConvention.INDEX_LEVEL,
                status=MarketStatus.WATCH,
            ),
            MarketDefinition(
                market_id="FX_RESEARCH",
                name="FX Research",
                market_type=MarketType.FX,
                region=ExchangeRegion.GLOBAL,
                default_currency="USD",
                timezone="UTC",
                quote_convention=QuoteConvention.RATE,
                status=MarketStatus.WATCH,
            ),
            MarketDefinition(
                market_id="CRYPTO_RESEARCH",
                name="Crypto Assets Research",
                market_type=MarketType.CRYPTO_RESEARCH,
                region=ExchangeRegion.GLOBAL,
                default_currency="USD",
                timezone="UTC",
                quote_convention=QuoteConvention.PRICE,
                status=MarketStatus.WATCH,
            ),
            MarketDefinition(
                market_id="MACRO_RESEARCH",
                name="Macroeconomic Indicators",
                market_type=MarketType.MACRO,
                region=ExchangeRegion.GLOBAL,
                default_currency="USD",
                timezone="UTC",
                quote_convention=QuoteConvention.PERCENT,
                status=MarketStatus.WATCH,
            ),
            MarketDefinition(
                market_id="SYNTHETIC_RESEARCH",
                name="Synthetic Assets",
                market_type=MarketType.CUSTOM,
                region=ExchangeRegion.SYNTHETIC,
                default_currency="SYN",
                timezone="UTC",
                quote_convention=QuoteConvention.PRICE,
                status=MarketStatus.WATCH,
            )
        ]

    def list_markets(self, status: Optional[MarketStatus] = None) -> List[MarketDefinition]:
        if not self._markets:
            for m in self.default_markets():
                self._markets[m.market_id] = m
        res = list(self._markets.values())
        if status:
            res = [m for m in res if m.status == status]
        return res

    def get_market(self, market_id_or_name: str) -> Optional[MarketDefinition]:
        if not self._markets:
            for m in self.default_markets():
                self._markets[m.market_id] = m
        for m in self._markets.values():
            if m.market_id == market_id_or_name or m.name == market_id_or_name:
                return m
        return None

    def register_market(self, market: MarketDefinition, confirm: bool = False) -> MarketDefinition:
        self._markets[market.market_id] = market
        if confirm and self.store:
            self.store.save_markets(list(self._markets.values()))
        return market

    def validate_market(self, market: MarketDefinition) -> List[str]:
        warnings = []
        if not market.name:
            warnings.append("Market name is empty")
        if not market.default_currency or len(market.default_currency) != 3 or not market.default_currency.isupper():
            warnings.append("Default currency must be 3 uppercase letters")
        if not market.timezone:
            warnings.append("Timezone is empty")
        return warnings

    def safe_market_summary(self, market: MarketDefinition) -> dict:
        return {
            "market_id": market.market_id,
            "name": market.name,
            "type": market.market_type.value,
            "status": market.status.value,
            "warnings": len(market.warnings),
            "disclaimer": market.disclaimer
        }
