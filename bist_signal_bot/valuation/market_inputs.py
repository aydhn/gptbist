import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import ValuationMarketInput

class ValuationMarketInputBuilder:
    def __init__(self,
                 settings: Optional[Settings] = None,
                 data_service: Any = None,
                 financials_engine: Any = None,
                 instrument_master: Any = None):
        self.settings = settings or Settings()
        self.data_service = data_service
        self.financials_engine = financials_engine
        self.instrument_master = instrument_master

    def build_input(self, symbol: str, as_of: Optional[datetime] = None) -> ValuationMarketInput:
        as_of = as_of or datetime.now(timezone.utc)
        warnings = []
        metadata = {}

        price = None
        price_source = None
        if self.data_service:
            # Fake/mock adapter logic would normally sit here or inside data_service
            # We assume it provides a dict with price for now
            price_data = self.data_service.get_latest_price(symbol, as_of=as_of)
            if price_data:
                price = price_data.get("close")
                price_source = price_data.get("source", "data_service")

        if price is None:
            warnings.append(f"Missing latest price for {symbol}")

        shares_outstanding = None
        free_float_ratio = None
        shares_source = None
        if self.instrument_master:
            record = self.instrument_master.get(symbol)
            if record:
                shares_outstanding = getattr(record, "shares_outstanding", None)
                free_float_ratio = getattr(record, "free_float_ratio", None)
                shares_source = "instrument_master"

        if shares_outstanding is None:
            warnings.append(f"Missing shares_outstanding for {symbol}")

        market_cap = self.calculate_market_cap(price, shares_outstanding)
        if market_cap is None and (price is not None or shares_outstanding is not None):
            warnings.append("Could not calculate market_cap")

        net_debt = None
        financial_ref = None
        if self.financials_engine:
            statement = self.financials_engine.get_latest_normalized_statement(symbol, as_of=as_of)
            if statement:
                financial_ref = statement.statement_id
                total_debt = getattr(statement, "total_debt", None)
                cash = getattr(statement, "cash_and_equivalents", None)
                net_debt = self.calculate_net_debt(total_debt, cash)

        ev = self.calculate_enterprise_value(market_cap, net_debt)

        inp = ValuationMarketInput(
            input_id=str(uuid.uuid4()),
            symbol=symbol,
            as_of=as_of,
            price=price,
            shares_outstanding=shares_outstanding,
            free_float_ratio=free_float_ratio,
            market_cap=market_cap,
            net_debt=net_debt,
            enterprise_value=ev,
            price_source=price_source,
            shares_source=shares_source,
            financial_statement_ref=financial_ref,
            warnings=warnings,
            metadata=metadata
        )

        inp.warnings.extend(self.validate_input(inp))
        return inp

    def calculate_market_cap(self, price: Optional[float], shares_outstanding: Optional[float]) -> Optional[float]:
        if price is not None and shares_outstanding is not None:
            return price * shares_outstanding
        return None

    def calculate_net_debt(self, total_debt: Optional[float], cash: Optional[float]) -> Optional[float]:
        if total_debt is not None and cash is not None:
            return total_debt - cash
        if total_debt is not None:
            return total_debt
        return None

    def calculate_enterprise_value(self, market_cap: Optional[float], net_debt: Optional[float]) -> Optional[float]:
        if market_cap is not None:
            return market_cap + (net_debt if net_debt is not None else 0.0)
        return None

    def validate_input(self, input: ValuationMarketInput) -> list[str]:
        warnings = []
        if input.price is None:
            warnings.append("Validation: Missing price.")
        if input.shares_outstanding is None:
            warnings.append("Validation: Missing shares_outstanding.")
        if input.market_cap is None:
            warnings.append("Validation: market_cap could not be computed.")
        if input.enterprise_value is None:
            warnings.append("Validation: enterprise_value could not be computed.")
        return warnings
