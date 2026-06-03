from typing import List, Optional
from bist_signal_bot.markets.models import CurrencyDefinition, MarketStatus

class CurrencyRegistry:
    def __init__(self, store=None):
        self.store = store
        self._currencies = {}

    def default_currencies(self) -> List[CurrencyDefinition]:
        return [
            CurrencyDefinition(currency_code="TRY", name="Turkish Lira", symbol="₺", precision=2, status=MarketStatus.ACTIVE),
            CurrencyDefinition(currency_code="USD", name="US Dollar", symbol="$", precision=2, status=MarketStatus.ACTIVE),
            CurrencyDefinition(currency_code="EUR", name="Euro", symbol="€", precision=2, status=MarketStatus.ACTIVE),
            CurrencyDefinition(currency_code="GBP", name="British Pound", symbol="£", precision=2, status=MarketStatus.ACTIVE),
            CurrencyDefinition(currency_code="XAU", name="Gold", symbol=None, precision=2, status=MarketStatus.ACTIVE),
            CurrencyDefinition(currency_code="SYN", name="Synthetic", symbol=None, precision=4, status=MarketStatus.ACTIVE),
        ]

    def get_currency(self, code: str) -> Optional[CurrencyDefinition]:
        if not self._currencies:
            for c in self.default_currencies():
                self._currencies[c.currency_code] = c
        return self._currencies.get(code.upper())

    def validate_currency(self, code: str) -> List[str]:
        warnings = []
        c = self.get_currency(code)
        if not c:
            warnings.append(f"Unknown currency: {code}")
        elif c.status != MarketStatus.ACTIVE:
            warnings.append(f"Currency {code} status is {c.status}")
        return warnings

    def currency_precision(self, code: str) -> Optional[int]:
        c = self.get_currency(code)
        return c.precision if c else None
