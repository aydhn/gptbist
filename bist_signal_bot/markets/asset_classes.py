from typing import List
from bist_signal_bot.markets.models import AssetClass, QuoteConvention

class AssetClassRegistry:
    def __init__(self, store=None):
        self.store = store

    def default_asset_classes(self) -> List[str]:
        return [a.value for a in AssetClass]

    def asset_class_for_market(self, market_id: str) -> AssetClass:
        if "EQUITY" in market_id.upper():
            return AssetClass.EQUITY
        if "FX" in market_id.upper():
            return AssetClass.CURRENCY_PAIR
        if "CRYPTO" in market_id.upper():
            return AssetClass.CRYPTO_ASSET_RESEARCH
        if "MACRO" in market_id.upper():
            return AssetClass.MACRO_INDICATOR
        if "INDEX" in market_id.upper():
            return AssetClass.INDEX
        return AssetClass.CUSTOM

    def validate_asset_class(self, asset_class: AssetClass) -> List[str]:
        if asset_class not in AssetClass:
            return ["Unknown asset class"]
        return []

    def quote_convention_for_asset(self, asset_class: AssetClass) -> QuoteConvention:
        mapping = {
            AssetClass.EQUITY: QuoteConvention.PRICE,
            AssetClass.ETF: QuoteConvention.PRICE,
            AssetClass.INDEX: QuoteConvention.INDEX_LEVEL,
            AssetClass.FUTURE: QuoteConvention.PRICE,
            AssetClass.CURRENCY_PAIR: QuoteConvention.RATE,
            AssetClass.CRYPTO_ASSET_RESEARCH: QuoteConvention.PRICE,
            AssetClass.MACRO_INDICATOR: QuoteConvention.PERCENT,
            AssetClass.FUND: QuoteConvention.PRICE,
            AssetClass.CASH: QuoteConvention.PRICE,
            AssetClass.CUSTOM: QuoteConvention.UNKNOWN,
        }
        return mapping.get(asset_class, QuoteConvention.UNKNOWN)
